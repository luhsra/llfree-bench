set -e

MIN_CPU=0
if [ -f "/sys/devices/system/cpu/intel_pstate/min_perf_pct" ]; then
    MIN_CPU=$(cat /sys/devices/system/cpu/intel_pstate/min_perf_pct)
fi

cleanup()
{
    echo reenable powersaving
    echo powersave | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
    if [ -f "/sys/devices/system/cpu/intel_pstate/min_perf_pct" ]; then
        echo $MIN_CPU >> /sys/devices/system/cpu/intel_pstate/min_perf_pct
    fi
}
trap cleanup EXIT HUP INT QUIT KILL SEGV TERM

echo disable powersaving
echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
if [ -f "/sys/devices/system/cpu/intel_pstate/min_perf_pct" ]; then
    echo 100 >> /sys/devices/system/cpu/intel_pstate/min_perf_pct
fi

sudo nice -n -20 sudo -u $SUDO_USER $@
