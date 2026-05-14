#!/bin/bash
# ===================================================
# InfinityPinger - Gerador de Pacote DEB (Linux)
# Execute este script a partir da pasta 'build'
# ===================================================

VERSION="0.2.0"
APP_NAME="infinitypinger"
ROOT_DIR=".."
DEB_DIR="deb_package"

echo "1. Limpando builds antigos..."
rm -rf dist build $DEB_DIR *.deb

echo "2. Instalando PyInstaller (caso nao tenha)..."
pip install pyinstaller

echo "3. Compilando binario Linux..."
# Roda na raiz para pegar o main.py
cd $ROOT_DIR
pyinstaller --noconfirm --onedir --windowed \
  --name "InfinityPinger" \
  --add-data "logo.png:." \
  "main.py"
cd build

echo "4. Preparando estrutura do pacote DEB..."
mkdir -p $DEB_DIR/DEBIAN
mkdir -p $DEB_DIR/opt/$APP_NAME
mkdir -p $DEB_DIR/usr/share/applications

# Copia o binario e dependencias
cp -r ../dist/InfinityPinger/* $DEB_DIR/opt/$APP_NAME/

# Cria arquivo de controle
cat <<EOF > $DEB_DIR/DEBIAN/control
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Orkestrae <contato@orkestrae.com>
Description: Ferramenta de monitoramento e diagnostico de rede.
 Alternativa multiplataforma, rapida e leve para visualizacao de latencia e LOZ.
EOF

# Cria atalho no menu de aplicativos (Desktop Entry)
cat <<EOF > $DEB_DIR/usr/share/applications/infinitypinger.desktop
[Desktop Entry]
Name=InfinityPinger
Comment=Monitoramento de Rede Orkestrae
Exec=/opt/$APP_NAME/InfinityPinger
Icon=/opt/$APP_NAME/logo.png
Terminal=false
Type=Application
Categories=Network;Utility;
EOF

# Permissoes corretas para o deb
chmod 755 $DEB_DIR/DEBIAN
chmod 755 $DEB_DIR/DEBIAN/control

echo "5. Construindo o arquivo .deb..."
dpkg-deb --build $DEB_DIR
mv ${DEB_DIR}.deb ../releases/${APP_NAME}_${VERSION}_amd64.deb

echo "Concluido! Pacote .deb gerado na pasta 'releases'."
