from flask import Flask, render_template, request, json
import subprocess
import os
import time
import logging

logging.basicConfig(filename='error.log', level=logging.DEBUG)

DUMPS_DIR = "DumpDir"
KEYFILE = "key-file.txt"
HOST = "localhost"
PORT = "5000"


def runCommand(command):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode


### Partie Flask (Serveur Web)
app = Flask('__name__', static_folder="res")
app.config['DEBUG'] = False


# Page principal
@app.route('/')
def root():
    if request.args.get("error"):  # On affiche l'erreur si il y en a une.
        error = request.args.get("error")
        return render_template('index.html', error=error)
    else:
        return render_template('index.html')


# Page d'attente du badge du client
@app.route('/waitingBadge')
def waitingBadge():
    nbBadge = request.args.get('nbBadge', default=1, type=int)
    return render_template('readBadge.html', nbBadge=nbBadge)


# Une fois que le badge est détecté
@app.route('/detectBadge')
def detectBadge():
    while True:  # Boucle infinie tant que le badge n'est pas detecté.
        stdout, stderr, return_code = runCommand('nfc-list')
        time.sleep(2)
        stdout = stdout.decode("utf-8")
        lines = stdout.split('\n')
        if "Interface opened" in lines[1]:
            if len(lines) > 6:
                badge_type = lines[4].replace('  ', ' ')
                if '00 04' in badge_type:
                    result = {'status': 'OK'}
                    break
                else:  # Si le badge n'est pas compatble avec le badge cloner.
                    result = {'status': 'ERROR', 'message': 'Badge non compatible !'}
                    break
        else:
            logging.warning(stdout.decode("utf-8"))
            result = {'status': 'ERROR', 'message': 'Lecteur NFC  non connecté !'}
            break
    return json.dumps(result)


# Permet de lire et copier le badge du client (Route appellée avec du JS depuis la page readBadge.html)
@app.route('/readBadge')
def readBadge():
    while True:  # Boucle infinie tant que le badge n'est pas detecté.
        stdout, stderr, return_code = runCommand('nfc-list')
        time.sleep(2)
        stdout = stdout.decode("utf-8")
        lines = stdout.split('\n')
        if "Interface opened" in lines[1]:
            if len(lines) > 6:
                badge_type = lines[4].replace('  ', ' ')
                if '00 04' in badge_type:
                    badge_UID = lines[5].replace('UID (NFCID1): ', '').replace(' ', '')
                     # Si un dump existe déjà pour cet UID et qu'il est complet
                    if ((os.path.isfile('%s/%s.dmp' % (DUMPS_DIR, badge_UID))) and (os.path.getsize('%s/%s.dmp' % (DUMPS_DIR, badge_UID)))) == 1024: 
                        result = {'status': 'OK', 'UID': badge_UID}
                        break
                    else:
                        stdout, stderr, status_code = runCommand(
                            'mfoc -f %s -P 500 -O %s/%s.dmp' % (KEYFILE, DUMPS_DIR, badge_UID))
                        time.sleep(2)
                        if status_code == 0:  # Si on a réussi à avoir le dump
                            if os.path.getsize('%s/%s.dmp' % (DUMPS_DIR, badge_UID)) == 1024:  # Mifare classic 1k
                                with open('%s/%s.dmp' % (DUMPS_DIR, badge_UID), 'rb') as f:
                                    hexdata = f.read().hex()
                                    sector11 = hexdata[1408:1536]  # On récupère le secteur 11
                                    if sector11[0:96] != "0" * 96:  # Si le secteur est pas vide
                                        result = {'status': 'ERROR', 'message': 'Badge protégé ! Ne pas copier !'}
                                        break
                                    else:
                                        result = {'status': 'OK', 'UID': badge_UID}
                                        break
                            else:
                                result = {'status': 'OK', 'UID': badge_UID}
                            break
                        else:
                            result = {'status': 'ERROR', 'message': 'Impossible de cracker le badge !'}
                            break
                else:  # Si le badge n'est pas compatble avec le badge cloner.
                    logging.warning(stdout.decode("utf-8"))
                    result = {'status': 'ERROR', 'message': 'Badge non compatible !'}
                    break
        else:
            logging.warning(stdout.decode("utf-8"))
            result = {'status': 'ERROR', 'message': 'Lecteur NFC  non connecté !'}
            break
    return json.dumps(result)


# Page d'attente des badges à cloner
@app.route('/writeBadge/<nbBadge>/<uid>')
def writeBadge(nbBadge, uid):
    if request.args.get("error"):  # On affiche l'erreur si il y en a une.
        error = request.args.get("error")
        return render_template('writeBadge.html', nbBadge=int(nbBadge), uid=uid, error=error)
    return render_template('writeBadge.html', nbBadge=int(nbBadge), uid=uid)


# Permet de cloner les badges
@app.route('/copyBadge/<uid>')
def copyBadge(uid):
    while True:  # Boucle infinie tant que le badge n'est pas detecté.
        stdout, stderr, return_code = runCommand('nfc-list')
        time.sleep(2)
        stdout = stdout.decode("utf-8")
        lines = stdout.split('\n')
        if "Interface opened" in lines[1]:
            if len(lines) > 6:
                badge_type = lines[4].replace('  ', ' ')
                if '00 04' in badge_type:
                    stdout, stderr, status_code = runCommand('mfoc -P 500 -O %s/new.dmp' % DUMPS_DIR)
                    time.sleep(2)
                    if status_code == 0:  # Si on a réussi à avoir le dump
                        stdout, stderr, status_code = runCommand(
                            'nfc-mfclassic W a %s/%s.dmp %s/new.dmp' % (DUMPS_DIR, uid, DUMPS_DIR))
                        time.sleep(2)
                        if status_code == 0:  # Si on a réussi à copier
                            result = {'status': 'OK', 'message': 'Badge copié !'}
                            break
                        else:
                            result = {'status': 'ERROR', 'message': 'Avez-vous mis un badge réinscriptible ?'}
                            break
                    else:
                        result = {'status': 'ERROR', 'message': 'Impossible d\'écrire sur ce badge'}
                        break
                else:  # Si le badge n'est pas compatble avec le badge cloner.
                    logging.warning(stdout.decode("utf-8"))
                    result = {'status': 'ERROR', 'message': 'Badge non compatible !'}
                    break
        else:
            logging.warning(stdout.decode("utf-8"))
            result = {'status': 'ERROR', 'message': 'Lecteur NFC  non connecté !'}
            break
    return json.dumps(result)


@app.route('/wait')
def wait():
    raison = request.args.get("raison")
    redirect = request.args.get("redirect")
    return render_template('wait.html', raison=raison, redirect=redirect)


app.run(host=HOST, port=PORT)
### Fin partie Flask ###
