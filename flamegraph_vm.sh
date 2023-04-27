# export PERF_EXEC_PATH=/srv/scratch/wrenger/nvalloc-linux/tools/perf
FLAMEGRAPH_PATH=/srv/scratch/wrenger/FlameGraph

OUT="flamegraph/memtier-nvalloc-t8"
# OUT="flamegraph/$(date '+%y%m%d_%H%M')"
# mkdir -p $OUT

# ssh -p5222 debian@localhost "sudo ./perf record -F 99 -ga -- $@"
# ssh -p5222 debian@localhost "sudo ./perf script" > $OUT/out.perf

$FLAMEGRAPH_PATH/stackcollapse-perf.pl --all $OUT/out.perf > $OUT/out.folded
$FLAMEGRAPH_PATH/flamegraph.pl $OUT/out.folded > $OUT/out.svg
