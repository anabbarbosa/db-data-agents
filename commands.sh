#!/bin/bash

# data agent - useful commands
# this file contains useful commands for managing the data agent

echo "🚀 data agent - useful commands"
echo "================================"

# function to show help
show_help() {
    echo ""
    echo "📋 available commands:"
    echo ""
    echo "🔧 installation:"
    echo "  ./commands.sh install     - install all dependencies"
    echo "  ./commands.sh check       - verify whether everything is installed"
    echo "  ./commands.sh update      - update all dependencies"
    echo ""
    echo "🗄️  database:"
    echo "  ./commands.sh setup-db    - configure the database"
    echo "  ./commands.sh etl-amazon  - run etl for amazon"
    echo "  ./commands.sh etl-spotify - run etl for spotify"
    echo ""
    echo "🌐 web server:"
    echo "  ./commands.sh start-web   - start the web server"
    echo "  ./commands.sh stop-web    - stop the web server"
    echo "  ./commands.sh restart-web - restart the web server"
    echo ""
    echo "🖥️  cli:"
    echo "  ./commands.sh cli-amazon  - run the amazon cli"
    echo "  ./commands.sh cli-spotify - run the spotify cli"
    echo ""
    echo "🧹 cleanup:"
    echo "  ./commands.sh clean       - remove temporary files"
    echo "  ./commands.sh reset       - full project reset"
    echo ""
}

# install dependencies
install_deps() {
    echo "📦 installing dependencies..."
    pip install -r requirements.txt
    echo "✅ installation completed!"
}

# verify installation
check_install() {
    echo "🔍 verifying installation..."
    python3 -c "
import flask, polars, pandas, sqlalchemy, psycopg2, requests, click, kagglehub
print('✅ all dependencies are installed!')
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

# update dependencies
update_deps() {
    echo "🔄 updating dependencies..."
    pip install --upgrade pip
    pip install --upgrade flask flask-cors polars pandas sqlalchemy psycopg2-binary requests click kagglehub
    echo "✅ update completed!"
}

# configure the database
setup_db() {
    echo "🗄️ configuring the database..."
    python3 main.py --etl 1 --agent 0
    echo "✅ database configured!"
}

# etl for amazon
etl_amazon() {
    echo "🛒 running amazon etl..."
    python3 main.py --etl 1 --agent 0 --user-group amazon
    echo "✅ amazon etl completed!"
}

# etl for spotify
etl_spotify() {
    echo "🎵 running spotify etl..."
    python3 main.py --etl 1 --agent 0 --user-group spotify
    echo "✅ spotify etl completed!"
}

# start the web server
start_web() {
    echo "🌐 starting the web server..."
    echo "access: http://localhost:5000"
    echo "credentials:"
    echo "  spotify: sa.spotify / admin_password_1"
    echo "  amazon: sa.amazon / admin_password_1"
    echo ""
    echo "press ctrl+c to stop the server"
    python3 -m data_agent.agent.template.app
}

# stop the web server
stop_web() {
    echo "🛑 stopping the web server..."
    pkill -f "data_agent.agent.template.app"
    echo "✅ server stopped!"
}

# restart the web server
restart_web() {
    echo "🔄 restarting the web server..."
    pkill -f "data_agent.agent.template.app"
    sleep 2
    echo "🌐 starting the web server..."
    python3 -m data_agent.agent.template.app &
    echo "✅ server restarted!"
}

# amazon cli
cli_amazon() {
    echo "🛒 starting the amazon cli..."
    python3 main.py --etl 0 --agent 1 --username sa.amazon --password admin_password_1
}

# spotify cli
cli_spotify() {
    echo "🎵 starting the spotify cli..."
    python3 main.py --etl 0 --agent 1 --username sa.spotify --password admin_password_1
}

# cleanup temporary files
clean() {
    echo "🧹 cleaning temporary files..."
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.log" -delete
    echo "✅ cleanup completed!"
}

# full project reset
reset() {
    echo "⚠️ attention: this will remove all data!"
    read -p "are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 running full reset..."
        pkill -f "data_agent.agent.template.app"
        clean
        echo "✅ reset completed!"
    else
        echo "❌ reset cancelled."
    fi
}

# process command arguments
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
        echo "❌ command not recognized: $1"
        show_help
        ;;
esac

