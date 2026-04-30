# Runbook: RAG Remote GPU Build (RunPod)

운영 절차서. R0~R4 phase별 단계별 명령 + 수동 fallback. plan v5 + worklog 970f83a + capability probe (`runpod-capability.md`)의 운영 결정을 그대로 반영.

**원칙 (worklog 970f83a, non-negotiable):**
- Pod은 *모든 path*에서 종료 (성공/실패/Ctrl-C 무관)
- API 키는 commit ❌, log ❌, echo 시 마스킹
- `holdout gate` 통과 전 production cutover ❌
- sampled 결과만으로 modality 글로벌 ON ❌

---

## 1. Prerequisites (한 번만 — 첫 R-phase 전)

### 1.1 의존성 설치

```bash
# RunPod SDK + CLI (둘 다 필요 — SDK는 programmatic, CLI는 send/receive)
.venv/bin/python -m pip install runpod
brew install runpod/runpodctl/runpodctl  # macOS
# 또는 https://github.com/runpod/runpodctl 에서 binary 다운로드
```

### 1.2 API 키 설정 (보안 주의)

```bash
# 옵션 A: env var (권장 — 셸 history 안 남음)
export RUNPOD_API_KEY="$(cat ~/.runpod/api_key)"

# 옵션 B: 파일 (gitignored)
mkdir -p ~/.runpod && chmod 700 ~/.runpod
echo "<api-key>" > ~/.runpod/api_key
chmod 600 ~/.runpod/api_key
```

`~/.runpod/`는 gitignored 경로. 절대 commit ❌.

### 1.3 비용 ledger 초기화

```bash
mkdir -p state/cs_rag_remote
[ -f state/cs_rag_remote/cost_ledger.json ] || echo '[]' > state/cs_rag_remote/cost_ledger.json
```

`state/cs_rag_remote/`는 gitignored.

### 1.4 Repo 상태 확인

```bash
git status                          # clean이어야 함
git rev-list --count origin/main..main  # 0이어야 함 (push 완료 상태)
```

push 안 된 상태면 **fallback 모드** (§3.2/§3.3).

---

## 2. Cost Ledger 사용

각 R-phase 실행 직전/직후 `bin/rag-remote-build`가 자동 갱신. 수동 확인:

```bash
# 누적 비용 + 살아있는 Pod 확인
.venv/bin/python -c "
import json
ledger = json.load(open('state/cs_rag_remote/cost_ledger.json'))
total = sum(r.get('estimated_cost_usd', 0) for r in ledger)
alive = [r for r in ledger if not r.get('deleted', False)]
print(f'총 누적: \${total:.2f}')
print(f'살아있는 Pod: {len(alive)}')
for r in alive:
    print(f'  - {r[\"run_id\"]}: pod_id={r[\"pod_id\"]} (gpu={r[\"gpu\"]})')
"
```

누적 $30 이상 → 사용자 컨펌 후 진행. R3 시작 전 안전 예산 잔액 확인 필수.

---

## 3. Repo 상태 원격 전송 (3 fallback)

### 3.1 1순위: git clone (정상 case)

push 완료 상태면 `bin/rag-remote-build`가 Pod에서 정확한 commit SHA로 clone:

```bash
# Pod 측 (자동 실행됨)
git clone https://github.com/DongKey777/woowa-learning-hub.git /workspace/repo
cd /workspace/repo
git checkout <COMMIT_SHA>
```

### 3.2 2순위: git bundle (private repo 또는 push 전 상태)

```bash
# 로컬
git bundle create /tmp/rag-build-${RUN_ID}.bundle --all

# Pod로 전송 (one-time code 방식 — API 키 ❌)
runpodctl send /tmp/rag-build-${RUN_ID}.bundle
# → "Code: a1b2c3d4" 출력. Pod 안에서:
#   runpodctl receive a1b2c3d4

# Pod 측에서
cd /workspace
git clone /tmp/rag-build-*.bundle repo
cd repo && git checkout <COMMIT_SHA>
```

### 3.3 3순위: source tarball (네트워크 제약 시)

```bash
# 로컬
git archive --format=tar.gz HEAD > /tmp/rag-source-${RUN_ID}.tar.gz

# Pod로 전송 (위와 동일 send/receive)
# Pod 측에서
mkdir -p /workspace/repo && tar -xzf /tmp/rag-source-*.tar.gz -C /workspace/repo
```

---

## 4. R0 — Infrastructure Smoke (~$0.15)

**목적:** RunPod 라이프사이클이 작동하는지 검증. bge-m3 로드 ❌, FTS-only.

```bash
bin/rag-remote-build \
    --r-phase r0 \
    --gpu-type "RTX A5000" \
    --gpu-cloud community \
    --max-cost 1.00 \
    --max-duration 30m
```

**자동 12-step:**
1. Repo 상태 확인 (clean OR commit SHA 기록)
2. push 확인 → 안 됐으면 bundle/tar fallback 활성
3. RunPod GPU Pod 생성 (A5000 Community)
4. SSH 키 생성 + 등록
5. Repo clone (또는 bundle/tar 업로드)
6. `pip install -e .` (lancedb, kiwipiepy 포함)
7. HF 캐시 warm — *FTS-only이므로 skip* ⚠️
8. `bin/cs-index-build --backend lance --modalities fts --out /workspace/cs_rag/`
9. Eval skip (R0는 smoke만)
10. `scripts/remote/package_rag_artifact.py` 로 tar.zst 생성
11. `runpodctl send` 또는 `scp`로 로컬 다운로드 → `artifacts/rag-full-build/${RUN_ID}/`
12. **Pod terminate + SSH 키 제거** (try/finally 보장)

**검증:**
```bash
ls artifacts/rag-full-build/${RUN_ID}/
# manifest.json, cs_rag_index_root.tar.zst, run.log, environment.json

# 로컬 압축 해제
mkdir -p /tmp/rag-r0-test
tar --use-compress-program=zstd -xf artifacts/rag-full-build/${RUN_ID}/cs_rag_index_root.tar.zst -C /tmp/rag-r0-test/

# manifest 확인
cat /tmp/rag-r0-test/manifest.json | jq '.encoder, .modalities, .lancedb.version'
```

**비용 reconciliation:**
```bash
# Ledger에 기록됐는지 확인
.venv/bin/python -m json.tool state/cs_rag_remote/cost_ledger.json | tail -20
# pod_id, deleted=true, estimated_cost_usd 모두 채워졌는지
```

---

## 5. R1 — bge-m3 Dense Full Build + Holdout (~$0.45)

**목적:** 첫 진짜 풀 코퍼스 vector index. dense의 holdout 검증.

### 5.1 1차 (max_length=512)

```bash
bin/rag-remote-build \
    --r-phase r1 \
    --gpu-type "RTX A5000" \
    --gpu-cloud community \
    --modalities fts,dense \
    --max-length 512 \
    --batch-size 64 \
    --fp16 \
    --max-cost 5.00 \
    --max-duration 90m
```

### 5.2 holdout 평가 (다운로드 후 로컬에서)

```bash
# 다운로드된 LanceDB 인덱스 root 압축 해제
mkdir -p state/cs_rag_eval/r1
tar --use-compress-program=zstd -xf artifacts/rag-full-build/${RUN_ID}/cs_rag_index_root.tar.zst \
    -C state/cs_rag_eval/r1/

# 인덱스 root 전체 (manifest.json + lance/ + chunk_hashes_per_model.json) 풀렸는지 확인
ls state/cs_rag_eval/r1/

# Holdout ablation (fts 단독 vs fts+dense)
bin/rag-eval --ablate \
    --embedding-index-root state/cs_rag_eval/r1/ \
    --ablation-split holdout \
    --ablation-modalities fts \
    --ablation-modalities fts,dense \
    --ablation-out reports/rag_eval/r1_holdout_${RUN_ID}.json
```

### 5.3 결정

```bash
# Report 검토
.venv/bin/python -c "
import json
r = json.load(open('reports/rag_eval/r1_holdout_${RUN_ID}.json'))
for combo in r['ablation_results']:
    print(combo['modalities'], '→ primary_nDCG@10 =', combo['primary_ndcg_macro'])
"
```

**Gate 통과 기준 (plan §H4 동일):**
- 전역 primary_nDCG@10 macro 베이스라인 대비 +0.005 이상 OR
- 한국어/beginner/코드 bucket 중 둘 이상 +0.02 이상 + 실패 회수율 +10%
- forbidden_rate 비악화
- warm P95 ≤ 500ms

**통과 시:** `lance_modalities_policy.json`에서 dense 활성 카테고리 holdout-confirmed 표시
**미통과 시:** dense baseline 유지, 사유 worklog에 기록 (R2는 *독립* 진행)

### 5.4 1024 max_length 재시도 (선택, 1차 결과 애매할 때만)

```bash
bin/rag-remote-build \
    --r-phase r1 \
    --tag retry-1024 \
    --max-length 1024 \
    --max-cost 5.00 \
    ...
```

추가 비용 ~$0.30. truncation 의심 케이스가 ~10% 이상이면 의미 있음.

---

## 6. R2 / R3 / R4 (간략)

**R2 (sparse):** R1 stack에 sparse 추가. 4-way ablation (fts / fts,sparse / fts,dense / fts,dense,sparse). plan §3 R2 참조.

**R3 (ColBERT):** 사용자 컨펌 후 진행. 가장 비쌈 ($1.00-2.25). A6000 Community 권장. plan §3 R3 참조.

**R4 (reranker A/B):** 빌드 ❌, eval만. R3 stack 위에 reranker swap. plan §3 R4 참조.

각 R-phase 명령 형태는 R1과 동일 패턴 (`--r-phase rN --modalities ... --max-cost ...`).

---

## 7. Manual Fallback (자동화 깨졌을 때)

### 7.1 Pod이 살아있는데 wrapper가 죽었음

```bash
# Orphan Pod 검출
.venv/bin/python -c "
import runpod, os
runpod.api_key = os.environ['RUNPOD_API_KEY']
pods = runpod.get_pods()
for p in pods:
    print(p['id'], p['name'], p['runtime']['uptimeInSeconds'])
"

# 수동 종료
.venv/bin/python -c "
import runpod, os
runpod.api_key = os.environ['RUNPOD_API_KEY']
runpod.terminate_pod('<pod_id>')
"

# 또는 runpodctl
runpodctl stop pod <pod_id>
```

### 7.2 SSH 접속

```bash
# 키 경로
ls /tmp/rag-pod-${RUN_ID}*

# Pod IP/포트 (Pod 정보에서)
ssh -i /tmp/rag-pod-${RUN_ID} root@<pod_ip> -p <pod_ssh_port>
```

### 7.3 Artifact 수동 회수

Pod이 살아있고 artifact가 Pod에 있을 때:

```bash
# 옵션 A: runpodctl send (Pod 측에서)
ssh -i /tmp/rag-pod-${RUN_ID} root@<pod_ip> -p <port> "runpodctl send /workspace/artifacts/rag-build.tar.zst"
# → 출력된 코드를 로컬에서:
runpodctl receive <code>

# 옵션 B: scp
scp -i /tmp/rag-pod-${RUN_ID} -P <port> root@<pod_ip>:/workspace/artifacts/rag-build.tar.zst ./
```

회수 후 Pod 종료 (§7.1).

### 7.4 SSH 키 잔여 정리

```bash
# 등록된 키 목록 확인
.venv/bin/python -c "
import runpod, os
runpod.api_key = os.environ['RUNPOD_API_KEY']
print(runpod.get_user())  # ssh_keys 포함
"

# 우리가 등록한 임시 키 (rag-build-*)는 모두 제거
# (안 하면 다음 R-phase에서 키 list가 무한 증가)
```

`bin/runpod-cleanup`이 이 절차를 자동화 (task v5-6의 일부로 작성).

### 7.5 비용 ledger 손상

```bash
# 백업 후 RunPod billing API와 양방향 reconcile
cp state/cs_rag_remote/cost_ledger.json state/cs_rag_remote/cost_ledger.backup.$(date +%s).json

# Reconciliation은 수동 (RunPod billing 대시보드 vs 로컬 ledger 비교)
```

---

## 8. Cutover Path (R0-R4 모두 통과 후만)

plan v5 §4 cutover gate 충족 시:

```bash
# 1. 기존 v2 인덱스 archive
cp -r state/cs_rag state/cs_rag_archive/v2_$(date +%Y%m%d)/

# 2. 다운받은 final stack artifact를 production 위치로 압축 해제
rm -rf state/cs_rag/lance state/cs_rag/manifest.json state/cs_rag/chunk_hashes_per_model.json
tar --use-compress-program=zstd -xf artifacts/rag-full-build/<final-run-id>/cs_rag_index_root.tar.zst \
    -C state/cs_rag/

# 3. config/rag_models.json 작성 (R-phase 결과 기반 stack 명시)
# (별도 명령 또는 수동 작성)

# 4. workbench 재시작 + smoke
HF_HUB_OFFLINE=1 bin/rag-ask "트랜잭션 격리수준"
# → top hit category=database 확인

# 5. (선택) Cutover regression 비교 report
.venv/bin/python scripts/learning/cli_rag_cutover_compare.py \
    --legacy reports/rag_eval/cutover_legacy_v2_${ts}.json \
    --lance reports/rag_eval/cutover_lance_${ts}.json \
    --out reports/rag_eval/cutover_legacy_vs_lance_${ts}.json
```

**Rollback (필요 시):** `state/cs_rag_archive/v2_<date>/`를 `state/cs_rag/`로 복원, workbench 재시작. 10분 이내.

---

## 9. 보안 체크리스트 (R-phase 시작 전마다)

- [ ] `~/.runpod/` 권한 700, 파일 600
- [ ] `RUNPOD_API_KEY` env var이 셸 history에 없음 (`history | grep RUNPOD` 결과 비어있음)
- [ ] `git diff --staged | grep -i "api_key\|api-key\|RUNPOD"` 결과 비어있음
- [ ] `~/.cache/huggingface/`가 gitignored (절대 commit ❌)
- [ ] `state/cs_rag_remote/` gitignored
- [ ] `/tmp/rag-pod-*` 임시 키 — 매 phase 후 자동 삭제됨

---

## 10. References

- `docs/worklogs/rag-remote-gpu-build-strategy-2026-04-30.md` — 전략 출처
- `docs/runbooks/runpod-capability.md` — capability probe 결과
- `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md` — v5 plan
- [RunPod docs](https://docs.runpod.io/)
- [runpod-python SDK](https://github.com/runpod/runpod-python)
- [runpodctl](https://github.com/runpod/runpodctl)
