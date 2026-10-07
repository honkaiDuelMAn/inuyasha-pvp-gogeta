var originalProbe = {};
originalProbe.bounds = function(clip) {
    if (clip == undefined) { return null; }
    var rect = clip.getBounds(_level0);
    return {x:(rect.xMin+rect.xMax)/2,y:(rect.yMin+rect.yMax)/2,width:rect.xMax-rect.xMin,height:rect.yMax-rect.yMin,visible:clip._visible,press:clip.onPress != undefined,release:clip.onRelease != undefined};
};
originalProbe.inspect = function() {
    var game = _level0.originalgame;
    var picker = game.viewPickMoves;
    var characterButtons = [];
    for (var characterId in game.viewPickCharacter._characterButtons) {
        var characterButton = game.viewPickCharacter._characterButtons[characterId].main_mc;
        var characterInfo = this.bounds(game.viewPickCharacter._characterButtons[characterId].portrait_mc);
        characterInfo.press = characterButton.onPress != undefined;
        characterInfo.id = characterId;
        characterButtons.push(characterInfo);
    }
    var slots = [];
    for (var row=0; row<picker._moveSelectorClips.length; row++) {
        for (var column=0; column<picker._moveSelectorClips[row].length; column++) {
            var clip = picker._moveSelectorClips[row][column];
            var info = this.bounds(clip);
            info.id = clip.moveId;
            info.art = clip.gogetaArt_mc != undefined;
            info.artWidth = clip.gogetaArt_mc._width;
            info.row = row;
            info.column = column;
            slots.push(info);
        }
    }
    var players = [];
    for (var index=0; index<2; index++) {
        var player = game.gameManager._players[index];
        var moves = [];
        if (player != undefined && player.moves != undefined) {
            for (var id in player.moves) {
                var move = player.moves[id];
                moves.push({id:id,advanced:move.advanced,energy:move.userImpact.energyDiff,damage:move.enemyImpact.lifeDiff});
            }
            players.push({character:player.characterId,life:player.life,energy:player.energy,loc:player.loc,moves:moves});
        } else {
            players.push(null);
        }
    }
    var versus = game.viewVersus._display_mc;
    return {
        userStats:game.userStatsManager.getStats(),
        characterButtons:characterButtons,
        roundsCount:game.gameManager._roundsCount,
        roundSummary:game.gameManager._roundSummary,
        players:players,
        pickerVisible:picker._display_mc._visible,
        slots:slots,
        continueButton:this.bounds(picker._continueButton_mc),
        versusVisible:versus._visible,
        fightButton:this.bounds(versus.panel_mc.button_fight_mc),
        roundVisible:game.viewRound._display_mc._visible
    };
};
flash.external.ExternalInterface.addCallback("originalTestState",originalProbe,originalProbe.inspect);
