var qualityProbe = {};
qualityProbe.state = function() {
    var game = _level0.pvpgame != undefined ? _level0.pvpgame : _level0.originalgame;
    var picker = game.viewPickMoves;
    var cards = [];
    var selectedCards = [];
    var revealCards = [];
    for (var row=0; row<picker._moveSelectorClips.length; row++) {
        for (var col=0; col<picker._moveSelectorClips[row].length; col++) {
            var clip = picker._moveSelectorClips[row][col];
            var bounds = clip.getBounds(_level0);
            cards.push({id:clip.moveId,row:row,column:col,frame:clip._currentframe,
                visible:clip._visible,press:clip.onPress != undefined,
                art:clip.gogetaArt_mc != undefined,artWidth:clip.gogetaArt_mc._width,
                artId:clip.gogetaMoveId,x:(bounds.xMin+bounds.xMax)/2,y:(bounds.yMin+bounds.yMax)/2});
        }
    }
    var figures = [];
    for (var revealIndex=0; revealIndex<2; revealIndex++) {
        var revealClip = game.viewRound._cardsDisplay_mc['card_'+revealIndex+'_fx_mc'];
        revealCards.push({id:revealClip.gogetaMoveId,frame:revealClip._currentframe,
            art:revealClip.gogetaArt_mc != undefined,alpha:revealClip._alpha});
    }
    for (var selectedIndex=0; selectedIndex<picker._selectedMovesClips.length; selectedIndex++) {
        var selectedClip = picker._selectedMovesClips[selectedIndex];
        selectedCards.push({id:selectedClip.gogetaMoveId,frame:selectedClip._currentframe,
            art:selectedClip.gogetaArt_mc != undefined});
    }
    var shells = [];
    var hud = [];
    var players = [];
    for (var index=0; index<2; index++) {
        var figure = game.viewRoundPlayers._playersClips[index].figure_mc;
        figures.push({frame:figure._currentframe,width:figure._width,height:figure._height,
            path:String(figure),move:game.viewRoundPlayers._currentMoves[index],
            linkage:game.viewRoundPlayers._attachProps[index].linkageId});
        var loaded = game.battleLoadManager._loadingShells[index];
        for (var layer in loaded) {
            var children = [];
            for (var key in loaded[layer]) {
                var child = loaded[layer][key];
                if (typeof(child) == "movieclip") { children.push(key); }
            }
            shells.push({index:index,layer:layer,children:children});
        }
        var status = game.viewPlayersStatus._playersClips[index];
        hud.push({nameFrame:status.name_mc._currentframe,portraitFrame:status.portrait_mc._currentframe,
            portraitArt:status.portrait_mc.gogetaPortrait_mc != undefined});
        var player = game.gameManager._players[index];
        players.push({character:player.characterId,life:player.life,energy:player.energy,loc:player.loc});
    }
    return {background:picker._display_mc.background_mc._currentframe,
        roundBackground:game.viewRound._display_mc.background_mc._currentframe,
        pickerVisible:picker._display_mc._visible,character:picker._player.characterId,
        cards:cards,selectedCards:selectedCards,revealCards:revealCards,figures:figures,shells:shells,hud:hud,
        rounds:game.gameManager._roundsCount,players:players,
        roundSummary:game.gameManager._roundSummary};
};
qualityProbe.observeAction = function(id) {
    var game = _level0.pvpgame != undefined ? _level0.pvpgame : _level0.originalgame;
    var library = game.battleLoadManager._loadingShells[0].top;
    stopAllSounds();
    this.events = [];
    library.qualityAction_mc.removeMovieClip();
    var clip = library.attachMovie("goMoves","qualityAction_mc",12001);
    clip._visible = false;
    clip.onMoveEvent = function(args) { qualityProbe.events.push({event:args.event,time:getTimer()}); };
    clip.gotoAndPlay(id);
    return clip != undefined;
};
qualityProbe.actionState = function() {
    var game = _level0.pvpgame != undefined ? _level0.pvpgame : _level0.originalgame;
    var clip = game.battleLoadManager._loadingShells[0].top.qualityAction_mc;
    return {frame:clip._currentframe,events:this.events};
};
qualityProbe.clearAction = function() {
    var game = _level0.pvpgame != undefined ? _level0.pvpgame : _level0.originalgame;
    game.battleLoadManager._loadingShells[0].top.qualityAction_mc.removeMovieClip();
};
qualityProbe.refresh = function() {
    var game = _level0.pvpgame != undefined ? _level0.pvpgame : _level0.originalgame;
    game.viewPickMoves._refresh();
    return this.state();
};
qualityProbe.clearSelection = function() {
    var game = _level0.pvpgame != undefined ? _level0.pvpgame : _level0.originalgame;
    game.viewPickMoves.clearSelectedMoves();
};
flash.external.ExternalInterface.addCallback("gogetaQualityState",qualityProbe,qualityProbe.state);
flash.external.ExternalInterface.addCallback("gogetaQualityRefresh",qualityProbe,qualityProbe.refresh);
flash.external.ExternalInterface.addCallback("gogetaQualityAction",qualityProbe,qualityProbe.observeAction);
flash.external.ExternalInterface.addCallback("gogetaQualityActionState",qualityProbe,qualityProbe.actionState);
flash.external.ExternalInterface.addCallback("gogetaQualityClearAction",qualityProbe,qualityProbe.clearAction);
flash.external.ExternalInterface.addCallback("gogetaQualityClearSelection",qualityProbe,qualityProbe.clearSelection);
