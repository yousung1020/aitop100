#!/usr/bin/env bash
set -euo pipefail

# EC2 배포 스크립트
# 사용법: ./scripts/deploy_to_ec2.sh <PEM_KEY_PATH> [USER]
# 예시: ./scripts/deploy_to_ec2.sh ~/.ssh/gyodong-key.pem ubuntu

PEM_KEY="${1:-}"
EC2_USER="${2:-ubuntu}"
EC2_IP="16.176.100.208"
REMOTE_DIR="/home/${EC2_USER}/gyodong-cs"

if [ -z "$PEM_KEY" ]; then
    echo "사용법: $0 <PEM_KEY_PATH> [USER (기본값: ubuntu)]"
    echo "예시: $0 ~/.ssh/my-key.pem ubuntu"
    exit 1
fi

if [ ! -f "$PEM_KEY" ]; then
    echo "오류: SSH 키 파일을 찾을 수 없습니다: $PEM_KEY"
    exit 1
fi

chmod 400 "$PEM_KEY"

echo "=== [1/4] EC2 (${EC2_USER}@${EC2_IP}) 원격 디렉터리 생성 ==="
ssh -i "$PEM_KEY" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_IP}" "mkdir -p ${REMOTE_DIR}"

echo "=== [2/4] 프로젝트 소스 및 설정 파일 동기화 ==="
rsync -avz --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' \
    -e "ssh -i $PEM_KEY -o StrictHostKeyChecking=no" \
    ./ "${EC2_USER}@${EC2_IP}:${REMOTE_DIR}/"

echo "=== [3/4] EC2 Docker 환경 점검 및 컨테이너 빌드 & 구동 ==="
ssh -i "$PEM_KEY" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_IP}" "bash -s" << 'EOF'
set -euo pipefail
cd ~/gyodong-cs

# Docker 설치 여부 확인 및 미설치 시 자동 설치
if ! command -v docker &> /dev/null; then
    echo "Docker 미설치 감지: 자동 설치를 진행합니다..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose-v2
    sudo usermod -aG docker $USER
fi

echo "컨테이너 빌드 및 백그라운드 구동..."
sudo docker compose down --remove-orphans || true
sudo docker compose up -d --build

echo "컨테이너 헬스체크 대기 (5초)..."
sleep 5
sudo docker compose ps
curl -s http://localhost:8000/health || echo "Health check response received"
EOF

echo "=== [4/4] 배포 완료! ==="
echo "서버 헬스체크 URL: http://${EC2_IP}:8000/health"
echo "스킬 웹훅 URL: http://${EC2_IP}:8000/skill"
