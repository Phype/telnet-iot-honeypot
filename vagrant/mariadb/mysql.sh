#/bin/bash

echo " - Install MariaDB"
sudo apt-get install -y mariadb-server

user=honey
db=honey
pw=$(openssl rand -hex 16)
sql="mysql+mysqldb://$user:$pw@localhost/$db"

echo " - Create DB"
echo ""
echo "DROP USER $user;"              | sudo mysql
echo "DROP USER '$user'@'localhost'" | sudo mysql
echo "DROP DATABASE $db;"            | sudo mysql
echo "CREATE USER '$user'@'localhost' IDENTIFIED BY '$pw';
CREATE DATABASE $db CHARACTER SET latin1 COLLATE latin1_swedish_ci;
GRANT ALL ON $db.* TO '$user'@'localhost';
FLUSH PRIVILEGES;
" | sudo mysql

echo " - Writing config"
echo sql: \"$sql\" >> config.yaml

