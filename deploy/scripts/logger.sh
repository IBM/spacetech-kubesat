log() {
	if [ "$1" == "1" ]; then
		echo -e "`date +'%Y-%m-%d %H:%M:%S,%N' \
      | sed 's/......$//g'` ${FUNCNAME[1]} - ERROR: $2" \
      2>&1 | tee -a $log
		echo -e "`date +'%Y-%m-%d %H:%M:%S,%N' \
      | sed 's/......$//g'` ${FUNCNAME[1]} - Exiting with errors." \
      2>&1 | tee -a $log
		exit 1
	else
		echo -e "`date +'%Y-%m-%d %H:%M:%S,%N' \
    | sed 's/......$//g'` ${FUNCNAME[1]} - $1" 2>&1 | tee -a $log
	fi
}
