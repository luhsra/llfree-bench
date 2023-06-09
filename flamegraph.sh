# export PERF_EXEC_PATH=/srv/scratch/wrenger/llfree-linux/tools/perf
FLAMEGRAPH_PATH=/srv/scratch/wrenger/FlameGraph

OUT="flamegraph/$(date '+%y%m%d_%H%M')"
mkdir -p $OUT

perf record -F 99 -ga -- $@
perf script > $OUT/out.perf

$FLAMEGRAPH_PATH/stackcollapse-perf.pl --all $OUT/out.perf > $OUT/out.folded
$FLAMEGRAPH_PATH/flamegraph.pl $OUT/out.folded > $OUT/out.svg
