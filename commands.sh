#!/bin/bash

# Data Agent - Comandos Úteis
# Este arquivo contém comandos úteis para gerenciar o Data Agent

echo "🚀 Data Agent - Comandos Úteis"
echo "================================"

# Função para mostrar ajuda
show_help() {
    echo ""
    echo "📋 COMANDOS DISPONÍVEIS:"
    echo ""
    echo "🔧 INSTALAÇÃO:"
    echo "  ./commands.sh install     - Instala todas as dependências"
    echo "  ./commands.sh check       - Verifica se tudo está instalado"
    echo "  ./commands.sh update      - Atualiza todas as dependências"
    echo ""
    echo "🗄️  BANCO DE DADOS:"
    echo "  ./commands.sh setup-db    - Configura o banco de dados"
    echo "  ./commands.sh etl-amazon  - Executa ETL para Amazon"
    echo "  ./commands.sh etl-spotify - Executa ETL para Spotify"
    echo ""
    echo "🌐 SERVIDOR WEB:"
    echo "  ./commands.sh start-web   - Inicia o servidor web"
    echo "  ./commands.sh stop-web    - Para o servidor web"
    echo "  ./commands.sh restart-web - Reinicia o servidor web"
    echo ""
    echo "🖥️  CLI:"
    echo "  ./commands.sh cli-amazon  - Executa CLI para usuário Amazon"
    echo "  ./commands.sh cli-spotify - Executa CLI para usuário Spotify"
    echo ""
    echo "🧹 LIMPEZA:"
    echo "  ./commands.sh clean       - Remove arquivos temporários"
    echo "  ./commands.sh reset       - Reset completo do projeto"
    echo ""
}

# Instalar dependências
install_deps() {
    echo "📦 Instalando dependências..."
    pip install -r requirements.txt
    echo "✅ Instalação concluída!"
}

# Verificar instalação
check_install() {
    echo "🔍 Verificando instalação..."
    python3 -c "
import flask, polars, pandas, sqlalchemy, psycopg2, requests, click, kagglehub
print('✅ Todas as dependências instaladas!')
print(f'Flask: {flask.__version__}')
print(f'Polars: {polars.__version__}')
print(f'Pandas: {pandas.__version__}')
print(f'SQLAlchemy: {sqlalchemy.__version__}')
print(f'psycopg2: {psycopg2.__version__}')
print(f'Requests: {requests.__version__}')
print(f'Click: {click.__version__}')
print(f'Kagglehub: {kagglehub.__version__}')
"
}

# Atualizar dependências
update_deps() {
    echo "🔄 Atualizando dependências..."
    pip install --upgrade pip
    pip install --upgrade flask flask-cors polars pandas sqlalchemy psycopg2-binary requests click kagglehub
    echo "✅ Atualização concluída!"
}

# Configurar banco de dados
setup_db() {
    echo "🗄️ Configurando banco de dados..."
    python3 main.py --etl 1 --agent 0
    echo "✅ Banco de dados configurado!"
}

# ETL Amazon
etl_amazon() {
    echo "🛒 Executando ETL Amazon..."
    python3 main.py --etl 1 --agent 0 --user-group amazon
    echo "✅ ETL Amazon concluído!"
}

# ETL Spotify
etl_spotify() {
    echo "🎵 Executando ETL Spotify..."
    python3 main.py --etl 1 --agent 0 --user-group spotify
    echo "✅ ETL Spotify concluído!"
}

# Iniciar servidor web
start_web() {
    echo "🌐 Iniciando servidor web..."
    echo "Acesse: http://localhost:5000"
    echo "Credenciais:"
    echo "  Spotify: sa.spotify / admin_password_1"
    echo "  Amazon:  sa.amazon  / admin_password_1"
    echo ""
    echo "Pressione Ctrl+C para parar o servidor"
    python3 -m db_data_agent.agent.template.app
}

# Parar servidor web
stop_web() {
    echo "🛑 Parando servidor web..."
    pkill -f "db_data_agent.agent.template.app"
    echo "✅ Servidor parado!"
}

# Reiniciar servidor web
restart_web() {
    echo "🔄 Reiniciando servidor web..."
    pkill -f "db_data_agent.agent.template.app"
    sleep 2
    echo "🌐 Iniciando servidor web..."
    python3 -m db_data_agent.agent.template.app &
    echo "✅ Servidor reiniciado!"
}

# CLI Amazon
cli_amazon() {
    echo "🛒 Iniciando CLI para usuário Amazon..."
    python3 main.py --etl 0 --agent 1 --username sa.amazon --password admin_password_1
}

# CLI Spotify
cli_spotify() {
    echo "🎵 Iniciando CLI para usuário Spotify..."
    python3 main.py --etl 0 --agent 1 --username sa.spotify --password admin_password_1
}

# Limpeza
clean() {
    echo "🧹 Limpando arquivos temporários..."
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.log" -delete
    echo "✅ Limpeza concluída!"
}

# Reset completo
reset() {
    echo "⚠️  ATENÇÃO: Isso irá remover todos os dados!"
    read -p "Tem certeza? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Fazendo reset completo..."
        pkill -f "db_data_agent.agent.template.app"
        clean
        echo "✅ Reset concluído!"
    else
        echo "❌ Reset cancelado."
    fi
}

# Processar argumentos
case "$1" in
    install)
        install_deps
        ;;
    check)
        check_install
        ;;
    update)
        update_deps
        ;;
    setup-db)
        setup_db
        ;;
    etl-amazon)
        etl_amazon
        ;;
    etl-spotify)
        etl_spotify
        ;;
    start-web)
        start_web
        ;;
    stop-web)
        stop_web
        ;;
    restart-web)
        restart_web
        ;;
    cli-amazon)
        cli_amazon
        ;;
    cli-spotify)
        cli_spotify
        ;;
    clean)
        clean
        ;;
    reset)
        reset
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Comando não reconhecido: $1"
        show_help
        ;;
esac
