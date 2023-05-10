# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

apt-get install -y jq

# Install the suitable kurtosis-cli
required_version=0.70.2
installed_version=`kurtosis version|grep -v WARN`

if [ "$installed_version" = "$required_version" ]; then
  echo "Kurtosis version is up to date : $installed_version"
else 
  echo "deb [trusted=yes] https://apt.fury.io/kurtosis-tech/ /" | sudo tee /etc/apt/sources.list.d/kurtosis.list
  sudo apt update
  sudo apt-mark unhold kurtosis-cli
  sudo apt install kurtosis-cli=$kurtosis_version
  sudo apt-mark hold kurtosis-cli
  sudo rm /etc/apt/sources.list.d/kurtosis.list
fi

# Build Gennet & WLS docker images

cd gennet-module
sh ./build_docker.sh
cd ..

cd wls-module
docker build -t wls:0.0.1 .
cd ..


git clone git@github.com:waku-org/go-waku.git
cd go-waku
docker build -t gowaku .
cd ..
rm -rf go-waku
