from flask import Flask, render_template, request, json
import subprocess
import os
import time

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
    else :
        return render_template('index.html')


# Page d'attente du badge du client
@app.route('/waitingBadge')
def waitingBadge():
    nbBadge = request.args.get('nbBadge', default=1, type=int)
    return render_template('waitingBadge.html', nbBadge=nbBadge)

# Une fois que le badge est détecté
@app.route('/detectBadge')
def detectBadge():
    while True:  # Boucle infinie tant que le badge n'est pas detecté.
        result = {'Error': '1'}
        stdout, stderr, return_code = runCommand('nfc-list')
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
        else :
            result = {'status': 'ERROR', 'message': 'Lecteur NFC  non connecté !'}
            break
    return json.dumps(result)

# Permet de lire et copier le badge du client (Route appellée avec du JS depuis la page waitingBadge.html)
@app.route('/readBadge')
def readBadge():
    while True:  # Boucle infinie tant que le badge n'est pas detecté.
        result = {'Error': '1'}
        stdout, stderr, return_code = runCommand('nfc-list')
        stdout = stdout.decode("utf-8")
        lines = stdout.split('\n')
        if "Interface opened" in lines[1]:
            if len(lines) > 6:
                badge_type = lines[4].replace('  ', ' ')
                if '00 04' in badge_type:
                    badge_UID = lines[5].replace('UID (NFCID1): ', '').replace(' ', '')
                    if os.path.isfile('%s/%s.dmp' %(DUMPS_DIR, badge_UID)) : #Si un dump existe déjà pour cet UID
                        result = {'status': 'OK', 'UID': badge_UID}
                        break
                    else :
                        stdout, stderr, status_code = runCommand('mfoc -f %s -P 500 -O %s/%s.dmp' %(KEYFILE, DUMPS_DIR, badge_UID))
                        if status_code == 0: #Si on a réussi à avoir le dump
                            result = {'status': 'OK', 'UID': badge_UID}
                            break
                        else :
                            result = {'status': 'ERROR', 'message': 'Impossible de cracker le badge !'}
                            break
                else:  # Si le badge n'est pas compatble avec le badge cloner.
                    result = {'status': 'ERROR', 'message': 'Badge non compatible !'}
                    break
        else :
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

#Permet de cloner les badges
@app.route('/copyBadge/<uid>')
def copyBadge(uid):
    while True:  # Boucle infinie tant que le badge n'est pas detecté.
        result = {'Error': '1'}
        stdout, stderr, return_code = runCommand('nfc-list')
        stdout = stdout.decode("utf-8")
        lines = stdout.split('\n')
        if "Interface opened" in lines[1]:
            if len(lines) > 6:
                badge_type = lines[4].replace('  ', ' ')
                if '00 04' in badge_type:
                    stdout, stderr, status_code = runCommand('mfoc -P 500 -O %s/new.dmp' %(DUMPS_DIR))
                    print(stdout)
                    print(status_code)
                    if status_code == 0: #Si on a réussi à avoir le dump
                        stdout, stderr, status_code = runCommand('nfc-mfclassic W a %s/%s.dmp %s/new.dmp' %(DUMPS_DIR, uid, DUMPS_DIR))
                        print(stdout)
                        print(status_code)
                        if status_code == 0: #Si on a réussi à copier
                            result = {'status': 'OK', 'message': 'Badge copié !'}
                            break
                        else :
                            result = {'status': 'ERROR', 'message': 'Avez-vous mis un badge réinscriptible ?'}
                            break
                    else :
                        result = {'status': 'ERROR', 'message': 'Impossible d\'écrire sur ce badge'}
                        break
                else:  # Si le badge n'est pas compatble avec le badge cloner.
                    result = {'status': 'ERROR', 'message': 'Badge non compatible !'}
                    break
        else :
            result = {'status': 'ERROR', 'message': 'Lecteur NFC  non connecté !'}
            break
    return json.dumps(result)

@app.route('/wait')
def wait():
    raison = request.args.get("raison")
    redirect = request.args.get("redirect")
    return render_template('wait.html',raison=raison, redirect=redirect)


app.run(host=HOST, port=PORT)
### Fin partie Flask ###
