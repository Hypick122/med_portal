sudo apt update && sudo apt upgrade

sudo apt install python3.11 -y
sudo apt install postgresql postgresql-contrib -y

wget https://www.pgadmin.org/static/packages_pgadmin_org.pub
apt-key add packages_pgadmin_org.pub
echo "deb https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list

sudo apt update && sudo apt install pgadmin4-web -y

sudo /usr/pgadmin4/bin/setup-web.sh

sudo -u postgres psql postgres
alter user postgres with password 'postgres';