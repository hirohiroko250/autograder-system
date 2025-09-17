#!/bin/bash

# デプロイスクリプト for Autograder System
# Usage: ./deploy.sh [production|staging]

set -e  # エラー時に停止

# 設定
PROJECT_NAME="autograder-system"
DEPLOY_USER="autograder"
DEPLOY_DIR="/opt/$PROJECT_NAME"
REPO_URL="https://github.com/hirohiroko250/autograder-system.git"
BRANCH="main"

# 環境設定
ENVIRONMENT=${1:-production}
echo "🚀 Starting deployment for environment: $ENVIRONMENT"

# 色付きログ用関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 前提条件チェック
check_prerequisites() {
    log_info "Checking prerequisites..."

    # ユーザー確認
    if ! id "$DEPLOY_USER" &>/dev/null; then
        log_error "User $DEPLOY_USER does not exist. Please create it first."
        exit 1
    fi

    # 必要なコマンドチェック
    for cmd in git python3 pip3 nginx systemctl; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is not installed"
            exit 1
        fi
    done

    log_info "Prerequisites check passed"
}

# アプリケーションコードのデプロイ
deploy_application() {
    log_info "Deploying application code..."

    # デプロイディレクトリ作成
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR

    # Git リポジトリクローンまたは更新
    if [ -d "$DEPLOY_DIR/.git" ]; then
        log_info "Updating existing repository..."
        cd $DEPLOY_DIR
        sudo -u $DEPLOY_USER git fetch origin
        sudo -u $DEPLOY_USER git reset --hard origin/$BRANCH
    else
        log_info "Cloning repository..."
        sudo -u $DEPLOY_USER git clone $REPO_URL $DEPLOY_DIR
        cd $DEPLOY_DIR
        sudo -u $DEPLOY_USER git checkout $BRANCH
    fi
}

# Python環境セットアップ
setup_python_environment() {
    log_info "Setting up Python environment..."

    cd $DEPLOY_DIR

    # 仮想環境作成
    if [ ! -d "venv" ]; then
        sudo -u $DEPLOY_USER python3 -m venv venv
    fi

    # 依存関係インストール
    sudo -u $DEPLOY_USER ./venv/bin/pip install --upgrade pip
    sudo -u $DEPLOY_USER ./venv/bin/pip install -r backend/requirements.txt
    sudo -u $DEPLOY_USER ./venv/bin/pip install gunicorn
}

# Django設定
setup_django() {
    log_info "Setting up Django..."

    cd $DEPLOY_DIR/backend

    # 環境変数設定
    export DJANGO_SETTINGS_MODULE="autograder.settings_production"

    # データベースマイグレーション
    sudo -u $DEPLOY_USER ../venv/bin/python manage.py migrate --noinput

    # 静的ファイル収集
    sudo -u $DEPLOY_USER ../venv/bin/python manage.py collectstatic --noinput

    # スーパーユーザー作成（初回のみ）
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Creating superuser (if not exists)..."
        sudo -u $DEPLOY_USER ../venv/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('Superuser created: admin / changeme123')
else:
    print('Superuser already exists')
"
    fi
}

# システムサービス設定
setup_services() {
    log_info "Setting up system services..."

    # ログディレクトリ作成
    sudo mkdir -p /var/log/autograder
    sudo chown $DEPLOY_USER:$DEPLOY_USER /var/log/autograder

    sudo mkdir -p /run/autograder
    sudo chown $DEPLOY_USER:$DEPLOY_USER /run/autograder

    # systemd サービスファイルコピー
    sudo cp $DEPLOY_DIR/deploy/autograder.service /etc/systemd/system/
    sudo systemctl daemon-reload

    # Nginx設定
    sudo cp $DEPLOY_DIR/deploy/nginx.conf /etc/nginx/sites-available/autograder
    sudo ln -sf /etc/nginx/sites-available/autograder /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
}

# サービス再起動
restart_services() {
    log_info "Restarting services..."

    # Gunicorn サービス
    sudo systemctl enable autograder
    sudo systemctl restart autograder

    # Nginx
    sudo nginx -t
    sudo systemctl enable nginx
    sudo systemctl restart nginx

    # サービス状態確認
    sleep 3
    if sudo systemctl is-active --quiet autograder; then
        log_info "✅ Autograder service is running"
    else
        log_error "❌ Autograder service failed to start"
        sudo systemctl status autograder
        exit 1
    fi

    if sudo systemctl is-active --quiet nginx; then
        log_info "✅ Nginx service is running"
    else
        log_error "❌ Nginx service failed to start"
        sudo systemctl status nginx
        exit 1
    fi
}

# ヘルスチェック
health_check() {
    log_info "Performing health check..."

    # Django アプリケーションの応答確認
    for i in {1..30}; do
        if curl -s http://localhost:8000/admin/ > /dev/null; then
            log_info "✅ Application is responding"
            break
        elif [ $i -eq 30 ]; then
            log_error "❌ Application failed to respond after 30 attempts"
            exit 1
        else
            log_warn "Waiting for application to start... (attempt $i/30)"
            sleep 2
        fi
    done
}

# メイン実行
main() {
    log_info "Starting deployment of $PROJECT_NAME"

    check_prerequisites
    deploy_application
    setup_python_environment
    setup_django
    setup_services
    restart_services
    health_check

    log_info "🎉 Deployment completed successfully!"
    log_info "📱 Application is available at: http://162.43.55.80/"
    log_info "🔧 Admin panel: http://162.43.55.80/admin/"

    if [ "$ENVIRONMENT" = "production" ]; then
        log_warn "⚠️  Don't forget to:"
        log_warn "   1. Change default admin password"
        log_warn "   2. Configure SSL/HTTPS"
        log_warn "   3. Set up monitoring"
        log_warn "   4. Configure backups"
    fi
}

# スクリプト実行
main "$@"