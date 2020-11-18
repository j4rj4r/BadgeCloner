# BadgeCloner
Projet permettant de créer un boitier qui va dupliquer des badges Vigik.
Il peut etre transporté ou etre utilisé dans un magasin pour vendre un service de badge cloné.

## Le matériel nécessaire :
- Un raspberry pi
- Un écran lcd tactile
- Un lecteur nfc acr122u
- Un clavier numérique (temporaire)

Le script peut aussi se lancer sur un ordinateur linux ayant accès à un lecteur nfc acr122u

## Dépendances du script :
- [Python 3.x](https://www.python.org/downloads/) : Qui permet de lancer le script.
- [Librarie Python Flask](https://pypi.org/project/Flask/) : Qui permet de mettre en place un serveur web et donc l'interface graphique dans ce projet.
- [Libnfc](http://nfc-tools.org/index.php/Libnfc)
- [MFOC](https://github.com/nfc-tools/mfoc)

## Installation :
Après avoir installé Python3.x, vous devez installer la librairie Flask.
```sh
$ python3 -m pip install flask
```
Vous pouvez ensuite télécharger le projet.
Pour que le script fonctionne correctement vous devez désactiver 2 modules (il est aussi possible d'enlever ces modules de facon permanente, un exemple [ici]( https://wiki.archlinux.org/index.php/Touchatag_RFID_Reader)).
```sh
$ sudo modprobe -r pn533_usb pn533
```
Mfoc et LibNFC peuvent etre installer avec ces commandes : 
```sh
$ sudo apt install libnfc*
$ sudo apt install mfoc
```
Vous devez créer le répertoire qui va stocker les dumps.
```sh
$ mkdir DumpDir
```
Pour lancer le projet au lancement du raspberry :
```sh
$ sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```
et vous devez ajouter ces commandes (vous pouvez ensuite fermer le fichier) : 
```
@sh /home/pi/launcher.sh &
@chromium-browser --incognito --kiosk http://localhost:5000
```
Pour finir il faut créer le fichier launcher.sh
```sh
$ nano ~/launcher.sh
```
et y ajouter ce texte :
```
cd /home/pi/BadgeCloner
python3 server.py
```
## Configuration :
Vous pouvez changer le nom du répertoire des dumps avec la variable
```
DUMPS_DIR
```
Pour renseigner une autre liste de clés
```
KEYFILE
```
Et changer le port du serveur
```
PORT
```
### Lancement et utilisation :
Pour lancer le script une commande suffit.
```sh
$ python3 server.py
```
L'url pour accéder à l'interface depuis le navigateur est :
```
localhost:PORT
```
PORT étant le numéro de port renseigné dans le script.
