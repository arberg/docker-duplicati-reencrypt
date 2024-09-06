
A Python script to change the encryption from Duplicati. You can go from aes to gpg or vice versa. It is also possible to remove encryption. 


## ReEncrypt info

The ReEncrypt script can be executed with and without --DELETE-ORIGINAL. If the process is interrupted it will start over from the beginning,
re-encrypting everything it finds in the orig folder again. If --DELETE-ORIGINAL is used, then the finished files will have been deleted from orig,
and thus not processed again. Therefore, it may be advantageous to use --DELETE-ORIGINAL simply for that reason, if you have a backup elsewhere.

Threading: By default the script now uses 2 threads. This seem fine on a Harddrive. On an SSD you might want to go higher. Note that each thread 
decompresses a dblock into a temp folder in the docker container instance, and thus also require extra space available in the docker container. The process 
will stop if it runs out of space. Thus the temp available space requirement in the docker container is atleast NoOfThreads * LargestDblockSize.

## Docker preparation

* Update /ReEncrypt, so that it mounts the desired volumes. By default its /mnt -> /mnt.
* Always test settings without '--DELETE-ORIGINAL', before running with --DELETE-ORIGINAL.

## Usage:
0) Ensure you have a backup of your data. Download your backups, for instance using rclone for cloud drive access.

1) Confirm that your Duplicati data is on disk in .zip or .zip.aes or .zip.gpg format..

2) Prepare a config file in /config, see example in config/config-sample-aes.json. 
    
    Note that hash-verification does NOT abort or print in an easy detectable way. To use it meaningfully pipe output to log-file and grep logfile 
    	cat out.log | grep "exact:" | grep -v "exact: True"

3) Run './ReEncrypt -c config/config.json | tee -a out.log'
	or './ReEncrypt -h'
	or './ReEncrypt -c config/config.json --DELETE-ORIGINAL'
		- but don't use --DELETE-ORIGINAL unless you have tested it works and can accept the risk of losing backups.

4) Update your duplicati backup settings to the changed encryption settings. 

5) The old database of the backup cannot be used, we must rebuild from the new reencrypted backup. Take a backup of your duplicati database and do a delete & recreate. Don't forget to delete, a simple "repair" may delete the whole backup! 


See https://github.com/duplicati/duplicati/wiki/Re-encrypt-remote-back-end-files

See https://github.com/duplicati/duplicati/tree/master/Tools/Commandline/ReEncrypt
