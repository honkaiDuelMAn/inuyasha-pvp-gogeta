// Reference source for the generated AVM1 events in go_figure.swf.
// tools/gogeta_figure.py emits equivalent bytecode directly so raster frame
// definitions and action labels remain deterministic.
function gogetaMoveEvent(kind) {
    this.onMoveEvent({event: kind});
}
