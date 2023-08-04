#!/usr/bin/env python3
## Copyright (C) 2018, The Duplicati Team
## http://www.duplicati.com, info@duplicati.com
##
## This library is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as
## published by the Free Software Foundation; either version 2.1 of the
## License, or (at your option) any later version.
##
## This library is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public
## License along with this library; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import sys, getopt
import io
import json
import zipfile
import base64
import hashlib
import pyAesCrypt
from collections import OrderedDict
from tempfile import mkstemp, mkdtemp, TemporaryFile, TemporaryDirectory, NamedTemporaryFile
import gnupg
import shutil
from joblib import Parallel, delayed
import multiprocessing

origDataPath=""
newDataPath=""
deleteOriginalBackup=False

def mainReEncrypt(options):
    # locate dlist
    dlists = [name for name in os.listdir(origDataPath) if name.endswith(".dlist.%s" %(options['orig']['extension']))]

    # loop over all dlists; they only need to be enencrypted, and encrypted. They have no relation to the dindex and dblock files.
    with NamedTemporaryFile() as temp_file:
        for dlist_enc in dlists:
            dlist_enc_fullpath = os.path.join(origDataPath,dlist_enc)
            dlist_reenc_fullpath = os.path.join(newDataPath,change_ext(dlist_enc,options['orig']['extension'],options['new']['extension']))
            decrypt(options['orig'],dlist_enc_fullpath,options['orig']['passwd'],temp_file.name)
            encrypt(options['new'],temp_file.name,options['new']['passwd'], dlist_reenc_fullpath)
            if (deleteOriginalBackup):
                deleteOrigFile(dlist_enc_fullpath)
                
        
    # locate dlist
    dindex = [name for name in os.listdir(origDataPath) if name.endswith(".dindex.%s" %(options['orig']['extension']))]

    num_cores = multiprocessing.cpu_count()
    Parallel(n_jobs=num_cores*2)(delayed(handleIndex)(options, dindex_enc) for dindex_enc in dindex)

def targetExists(options, dfile):
    return os.path.exists(os.path.join(newDataPath, dfile))

def handleIndex(options, dindex_enc):
    with NamedTemporaryFile() as temp_dindex, NamedTemporaryFile() as temp_dindex_reenc, TemporaryDirectory() as temp_path_zip:
        dindex_enc_fullpath = os.path.join(origDataPath,dindex_enc)
        dindex_reenc_fullpath = os.path.join(newDataPath,change_ext(dindex_enc,options['orig']['extension'],options['new']['extension']))
        
        decrypt(options['orig'],dindex_enc_fullpath,options['orig']['passwd'],temp_dindex.name)
            
        unzip(temp_dindex,temp_path_zip)

        origFilesList = []
        vol_path = os.path.join(temp_path_zip,'vol')
        if os.path.exists(vol_path):
            # The vol dir contains info-files named identically to the dblock files
            for dblock in os.listdir(vol_path):
                data = []

                # dblock original and new file
                dblock_enc_fullpath = os.path.join(origDataPath,dblock)
                dblock_reenc_filename = change_ext(dblock,options['orig']['extension'],options['new']['extension'])
                dblock_reenc_fullpath = os.path.join(newDataPath, dblock_reenc_filename)
                origFilesList.append(dblock_enc_fullpath)
                
                # tmp dblock info file to be updated
                tmp_info_dblockFile=os.path.join(vol_path, dblock)
				#  Load the index json file, so we can modify the dblock references
                with open(tmp_info_dblockFile) as data_file:
                    data = json.load(data_file, object_pairs_hook=OrderedDict)

                expected_hash = data['volumehash'].encode('utf8')
                expected_volumesize = data['volumesize']

                if (options['verify_hash']):
                    actual_hash = computeHash(dblock_enc_fullpath)
                    actual_volumesize=os.stat(dblock_enc_fullpath).st_size
                    print('dblock: %s expected_hash: %s calc_hash: %s exact: %s' % (dblock,expected_hash.decode('utf8'),actual_hash.decode('utf8'),expected_hash==actual_hash))

                with NamedTemporaryFile() as temp_dblock:
                    decrypt(options['orig'],dblock_enc_fullpath,options['orig']['passwd'],temp_dblock.name)
                    encrypt(options['new'],temp_dblock.name,options['new']['passwd'], dblock_reenc_fullpath)
                    new_hash = computeHash(dblock_reenc_fullpath)
                    
                data['volumehash'] = new_hash.decode('utf8')
                data['volumesize'] = os.stat(dblock_reenc_fullpath).st_size
                print('dblock: %s old_hash: %s new_hash: %s' % (dblock,expected_hash.decode('utf8'),data['volumehash']))

				# Dump the updated index json file, so we can modify the dblock references
                with open(tmp_info_dblockFile,'w') as data_file:
                    json.dump(data, data_file)
                # Rename dblock-info file to new extension, matching the actual dblock file
                os.rename(tmp_info_dblockFile, os.path.join(vol_path, dblock_reenc_filename)) 
        
        make_zipfile(temp_dindex_reenc.name,temp_path_zip)
        encrypt(options['new'], temp_dindex_reenc.name, options['new']['passwd'], dindex_reenc_fullpath)
        origFilesList.append(dindex_enc_fullpath)
        
        if (deleteOriginalBackup):
            for file in origFilesList:
                deleteOrigFile(file)

def deleteOrigFile(file):
    # os.rename(file, file+".deleted") # Just renames file, simulating delete
    os.remove(file)

def change_ext(filename, ext_old, ext_new):
    return filename.replace(ext_old, ext_new)

def decrypt(options, encrypted, passw, decrypted):
    print('decrypting: %s to %s' % (encrypted, decrypted))
    if options['encryption']=='aes':
        bufferSize = 64 * 1024
        pyAesCrypt.decryptFile(encrypted, decrypted, passw, bufferSize)
    if options['encryption']=='gpg':
        gpg = gnupg.GPG()
        with open(encrypted, 'rb') as f:
            status  = gpg.decrypt_file(f, output=decrypted,passphrase=passw)
    if options['encryption']=='none':
        shutil.copy(encrypted,decrypted)
    

def encrypt(options,decrypted, passw, encrypted):
    print('encrypting: %s %s' % (decrypted, encrypted))
    if options['encryption']=='aes':
        bufferSize = 64 * 1024
        pyAesCrypt.encryptFile(decrypted, encrypted, passw, bufferSize)
    if options['encryption']=='gpg':
        gpg = gnupg.GPG()
        with open(decrypted, 'rb') as f:
            status  = gpg.encrypt_file(f, recipients=options['recipients'], output=encrypted, armor=False)
    if options['encryption']=='none':
        shutil.copy(decrypted,encrypted)

def emptydir(top):
    if(top == '/' or top == "\\"): return
    else:
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

def unzip(archive, path):
    emptydir(path)
    with zipfile.ZipFile(archive.name) as zf:
        zf.extractall(path)

def make_zipfile(output_filename, source_dir):
    print('zipping: %s to %s' % (source_dir, output_filename))
    emptydir(output_filename)
    relroot=source_dir
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)
                    

def rezip(temp_path_z, path):
    zf = zipfile.ZipFile(path, "w")
    for dirname, subdirs, files in os.walk(temp_path_z):
        zf.write(dirname)
        for filename in files:
            zf.write(os.path.join(dirname, filename))
    zf.close()

def zipdir(path,ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
            
def computeHash(path):
    print('hashing: %s ' % (path))
    buffersize=64 * 1024
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            buffer = f.read(buffersize)
            if not buffer:
                break
            hasher.update(buffer)
    return base64.b64encode(hasher.digest())

def printUsage():
    print('ReEncrypt.py -c <configfile> [--DELETE-ORIGINAL]')

def main(argv):
    configfile = ''
    deleteOption='DELETE-ORIGINAL'
    try:
        opts, args = getopt.getopt(argv,"hc:", [deleteOption])
    except getopt.GetoptError:
        printUsage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printUsage()
            sys.exit(2)
        elif opt == '-c':
            configfile = arg
        elif opt == "--"+deleteOption:
            print("##############################################################################################")
            print("### WARNING: The original backup will be deleted. PLEASE DO NOT do this unless you need to ###")
            print("### and have tested your config script works (and are willing to risk losing your backups) ###")
            print("##############################################################################################")
            global deleteOriginalBackup
            deleteOriginalBackup = True # Sleep below after parsing config to give user a brief time to abort
        else:
            print( "unhandled option: "+opt)
    if (configfile == ''):
        print("Config file not specified")
        printUsage()
        sys.exit(2)
    if not os.path.exists(configfile):
        print("Config file not found: "+configfile)
        sys.exit(2)
    with open(configfile) as infile:
        options = json.load(infile)
        global origDataPath
        global newDataPath
        origDataPath=options['orig']['path']
        newDataPath=options['new']['path']
        if newDataPath == origDataPath:
            print("ERROR: new and orig path are identical")
            sys.exit(2)
        if not os.path.exists(origDataPath):
            print("Original data path not found: "+origDataPath)
            sys.exit(2)
        # Create target dir
        if not os.path.exists(newDataPath):
            os.mkdir(newDataPath)
        if not os.path.exists(newDataPath):
            print("New data path not found (and could not create): "+newDataPath)
            sys.exit(2)
        if deleteOriginalBackup:
            import time
            time.sleep(5)

        mainReEncrypt(options)
    print('Complete.')

if __name__ == "__main__":
   main(sys.argv[1:])

