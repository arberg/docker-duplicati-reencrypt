
A Python script to change the encryption from Duplicati. You can go from aes to gpg or vice versa. It is also possible to remove encryption. 

Usage:
0) Ensure you have a backup of your data. Download your backups, for instance using rclone for cloud drive access.

1) Confirm that your Duplicati data is on disk in .zip or .zip.aes or .zip.gpg format..

2) Prepare a config file in /config, see example in config/config-sample.txt. 
    
    Note that hash-verification does NOT abort or print in an easy detectable way. To use it meaningfully pipe output to log-file and grep logfile 
    	cat out.log | grep "exact:" | grep -v "exact: True"

3) Run './ReEncrypt -c config/config.txt | tee -a out.log'
	or './ReEncrypt -h'
	or './ReEncrypt -c config/config.txt --DELETE-ORIGINAL'
		- but don't use --DELETE-ORIGINAL unless you have tested it works and can accept the risk of losing backups.

4) Update your duplicati backup settings to the changed encryption settings. 

5) The old database of the backup cannot be used, we must rebuild from the new reencrypted backup. Take a backup of your duplicati database and do a delete & recreate. Don't forget to delete, a simple "repair" may delete the whole backup! 


See https://github.com/duplicati/duplicati/wiki/Re-encrypt-remote-back-end-files

See https://github.com/duplicati/duplicati/tree/master/Tools/Commandline/ReEncrypt