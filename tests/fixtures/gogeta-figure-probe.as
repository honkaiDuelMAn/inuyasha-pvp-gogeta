stop();
flash.external.ExternalInterface.addCallback("gogetaFigureReady", this, function() {
    return {_currentframe:_root._currentframe,_framesloaded:_root._framesloaded};
});
