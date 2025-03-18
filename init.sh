sed -i "/^HOST/s/=.*$/=$(hostname)/" .env

docker-compose up