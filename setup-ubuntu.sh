#!/bin/bash

# ===============================================
# Script de Instalação - Projeto Flask no Ubuntu 24.04
# ===============================================
# Este script automatiza toda a configuração do projeto no servidor

set -e  # Parar em caso de erro

echo "=========================================="
echo "Iniciando setup do Projeto Flask"
echo "=========================================="

# ===============================================
# 1. ATUALIZAR REPOSITÓRIOS E INSTALAR DEPENDÊNCIAS
# ===============================================
echo ""
echo "[1/10] Atualizando repositórios e instalando dependências do sistema..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv build-essential libssl-dev libffi-dev python3-dev git nginx supervisor

# ===============================================
# 2. PREPARAR DIRETÓRIO DO PROJETO
# ===============================================
echo ""
echo "[2/10] Preparando diretório do projeto..."
cd /var/www

# Se o repositório não existe, clonar
if [ ! -d "Projeto-Integrador-UNIVESP" ]; then
    echo "Clonando repositório..."
    sudo git clone https://github.com/Kauee01/Projeto-Integrador-UNIVESP.git
fi

sudo chown -R $USER:$USER Projeto-Integrador-UNIVESP
cd Projeto-Integrador-UNIVESP

# ===============================================
# 3. CRIAR E ATIVAR AMBIENTE VIRTUAL
# ===============================================
echo ""
echo "[3/10] Criando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# ===============================================
# 4. INSTALAR DEPENDÊNCIAS PYTHON
# ===============================================
echo ""
echo "[4/10] Instalando dependências Python..."
# Criar uma versão do requirements sem pacotes Windows-only (pywin32)
if [ -f requirements.txt ]; then
    echo "Removendo pacotes específicos do Windows do requirements (ex: pywin32)..."
    grep -v -i '^pywin32' requirements.txt > requirements-linux.txt || cp requirements.txt requirements-linux.txt
    echo "Instalando pacotes a partir de requirements-linux.txt"
    pip install -r requirements-linux.txt
else
    echo "Atenção: requirements.txt não encontrado. Pulando instalação de dependências do projeto."
fi

# Instalar gunicorn separadamente (garante que exista)
pip install gunicorn

# ===============================================
# 5. PREPARAR BANCO DE DADOS
# ===============================================
echo ""
echo "[5/10] Preparando banco de dados..."
python3 << 'EOF'
from app import app, db

with app.app_context():
    db.create_all()
    print("✓ Banco de dados criado com sucesso!")
EOF

# ===============================================
# 6. DESATIVAR DEBUG MODE
# ===============================================
echo ""
echo "[6/10] Ajustando configuração de produção..."
# Backup do arquivo original
cp app.py app.py.backup

# Substituir debug=True por debug=False
sed -i 's/app\.run(debug=True)/app.run(debug=False)/g' app.py
echo "✓ Debug mode desativado"

# ===============================================
# 7. CONFIGURAR SUPERVISOR
# ===============================================
echo ""
echo "[7/10] Configurando Supervisor..."

PROJECT_PATH=$(pwd)

sudo tee /etc/supervisor/conf.d/flask-app.conf > /dev/null <<EOF
[program:flask-app]
directory=$PROJECT_PATH
command=$PROJECT_PATH/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/flask-app.err.log
stdout_logfile=/var/log/flask-app.out.log
user=www-data
environment=PATH="$PROJECT_PATH/venv/bin"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flask-app
echo "✓ Supervisor configurado e iniciado"

# ===============================================
# 8. CONFIGURAR NGINX
# ===============================================
echo ""
echo "[8/10] Configurando Nginx..."

# Obter IP ou usar localhost
HOSTNAME=$(hostname -I | awk '{print $1}')
if [ -z "$HOSTNAME" ]; then
    HOSTNAME="localhost"
fi

sudo tee /etc/nginx/sites-available/flask-app > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    location /static {
        alias /var/www/Projeto-Integrador-UNIVESP/static;
        expires 30d;
    }
}
EOF

# Habilitar configuração
if [ -e /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

sudo ln -sf /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
echo "✓ Nginx configurado"

# ===============================================
# 9. AJUSTAR PERMISSÕES
# ===============================================
echo ""
echo "[9/10] Ajustando permissões..."
sudo chown -R www-data:www-data /var/www/Projeto-Integrador-UNIVESP
sudo chmod -R 755 /var/www/Projeto-Integrador-UNIVESP
sudo chmod -R 775 /var/www/Projeto-Integrador-UNIVESP/instance
echo "✓ Permissões ajustadas"

# ===============================================
# 10. CONFIGURAR FIREWALL (Opcional)
# ===============================================
echo ""
echo "[10/10] Configurando firewall (UFW)..."
sudo ufw allow 22/tcp > /dev/null 2>&1
sudo ufw allow 80/tcp > /dev/null 2>&1
sudo ufw --force enable > /dev/null 2>&1
echo "✓ Firewall configurado"

# ===============================================
# RESUMO FINAL
# ===============================================
echo ""
echo "=========================================="
echo "✓ Setup concluído com sucesso!"
echo "=========================================="
echo ""
echo "📊 INFORMAÇÕES DO SERVIDOR:"
echo "  URL da aplicação: http://$HOSTNAME/"
echo "  Health check: http://$HOSTNAME/health"
echo "  Projeto localizado em: /var/www/Projeto-Integrador-UNIVESP"
echo ""
echo "🔧 COMANDOS ÚTEIS:"
echo "  Verificar status: sudo supervisorctl status flask-app"
echo "  Ver logs da app: tail -f /var/log/flask-app.out.log"
echo "  Reiniciar app: sudo supervisorctl restart flask-app"
echo "  Ver logs do Nginx: sudo tail -f /var/log/nginx/error.log"
echo "  Status Nginx: sudo systemctl status nginx"
echo ""
echo "⚠️  PRÓXIMOS PASSOS:"
echo "  1. Teste a aplicação em http://$HOSTNAME"
echo "  2. Configure seu domínio (DNS)"
echo "  3. Configure HTTPS com Let's Encrypt (opcional)"
echo ""
echo "=========================================="
