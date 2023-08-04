
A Python script to change the encryption from Duplicati. You can go from aes to gpg or vice versa. It is also possible to remove encryption. 

Usage:
0) Ensure you have a backup of your data. Download your backups, for instance using rclone for cloud drive access.

1) Confirm that your Duplicati data is on disk in .zip or .zip.aes or .zip.gpg format..

3) Prepare a config file in /config, see example in config/config-sample.txt. 

3) Run './run.sh' which runs 'ReEncrypt.sh -c config/config.txt.'

4) Update your duplicati backup settings to the changed encryption settings. 

5) The old database of the backup cannot be used, we must rebuild from the new reencrypted backup. Take a backup of your duplicati database and do a delete & recreate. Don't forget to delete, a simple "repair" may delete the whole backup! 


See https://github.com/duplicati/duplicati/wiki/Re-encrypt-remote-back-end-files

See https://github.com/duplicati/duplicati/tree/master/Tools/Commandline/ReEncrypt