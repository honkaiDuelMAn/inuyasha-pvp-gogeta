stop();
var gameRoot = _level0;
var g = gameRoot.pvpgame;
var b = gameRoot.pvpBridge = {seat:0, match:0, round:0, phase:"selecting", timer:0};
var ei = flash.external.ExternalInterface;
b.emit = function(kind, data) { flash.external.ExternalInterface.call("pvpEvent", kind, data); };
b.arrayHas = function(values, target) {
    for (var i=0; i<values.length; i++) { if (values[i] == target) { return true; } }
    return false;
};
// BEGIN SHARED GOGETA DISPLAY
// Shared display hooks, expanded into both bridge sources by the build tool.
b.gogetaCardImages = {
    bigBangKamehameha:true,dragonFist:true,superEnergyBackflow:true,superKamehameha:true,
    guard:true,energyUp:true,moveLeft:true,moveRight:true,moveUp:true,moveDown:true,
    perfectGuard:true,heal:true,kikyosRevenge:true,doubleRight:true,doubleLeft:true,summonShippo:true
};
b.gogetaBitmapCache = {};
b.bitmap = function(id) {
    if (this.gogetaBitmapCache[id] == undefined) {
        this.gogetaBitmapCache[id] = flash.display.BitmapData.loadBitmap("goBitmap_"+id);
    }
    return this.gogetaBitmapCache[id];
};
b.clearGogetaCardArt = function(clip) {
    if (clip != undefined && clip.gogetaArt_mc != undefined) {
        clip.gogetaArt_mc.removeMovieClip();
        clip.gogetaTint_mc.removeMovieClip();
        delete clip.gogetaMoveId;
    }
};
b.decorateGogetaCard = function(view, clip, moveId) {
    if (clip == undefined) { return; }
    if (!this.gogetaCardImages[moveId]) { this.clearGogetaCardArt(clip); return; }
    // Embedded art is synchronous. A refresh retains the existing instance.
    if (clip.gogetaMoveId != moveId || clip.gogetaArt_mc == undefined) {
        this.clearGogetaCardArt(clip);
        var art = clip.createEmptyMovieClip("gogetaArt_mc",1000);
        art.attachBitmap(this.bitmap(moveId),1,"always",false);
        clip.gogetaMoveId = moveId;
        clip.gogetaArt_mc.enabled = false;
        clip.gogetaArt_mc.useHandCursor = false;
        if (clip.tinter_mc != undefined) {
            clip.tinter_mc.duplicateMovieClip("gogetaTint_mc",1001);
        }
    }
    if (clip.gogetaTint_mc != undefined) {
        clip.gogetaTint_mc.gotoAndStop(clip.tinter_mc._currentframe);
    }
};
b.decorateGogetaMoveCards = function(view) {
    for (var rowIndex=0; rowIndex<view._moveSelectorClips.length; rowIndex++) {
        var row = view._moveSelectorClips[rowIndex];
        for (var column=0; column<row.length; column++) {
            var clip = row[column];
            if (view._player.characterId == "go" && clip._visible &&
                !view._isMoveSelected({move:view._playerMoves[clip.moveId]})) {
                this.decorateGogetaCard(view,clip,clip.moveId);
            } else { this.clearGogetaCardArt(clip); }
        }
    }
};
b.decorateGogetaSelectedCards = function(view) {
    for (var index=0; index<view._selectedMovesClips.length; index++) {
        var clip = view._selectedMovesClips[index];
        var selected = view._selectedMoves[index];
        if (view._player.characterId == "go" && selected != 0) {
            this.decorateGogetaCard(view,clip,selected.id);
        } else { this.clearGogetaCardArt(clip); }
    }
};
b.showGogetaPortrait = function(clip, size) {
    if (clip.gogetaPortrait_mc == undefined) {
        var art = clip.createEmptyMovieClip("gogetaPortrait_mc",1000);
        art.attachBitmap(this.bitmap("portrait"),1,"always",false);
    }
    clip.gogetaPortrait_mc._xscale = size/120*100;
    clip.gogetaPortrait_mc._yscale = size/120*100;
};
b.backgroundChildren = function(clip, playing) {
    for (var key in clip) {
        var child = clip[key];
        if (typeof(child) == "movieclip" && child._parent == clip) {
            if (playing) { child.play(); } else { child.stop(); }
            this.backgroundChildren(child,playing);
        }
    }
};
b.installGogetaDisplay = function() {
    if (this.gogetaDisplayInstalled) { return; }
    this.gogetaDisplayInstalled = true;
    var picker = g.viewPickMoves;
    picker.gogetaNativeMoveLabel = picker._generateMoveLabelName;
    picker._generateMoveLabelName = function(args) {
        if (args.characterId != "go") { return this.gogetaNativeMoveLabel.call(this,args); }
        var id = args.moveId;
        if (id == "bigBangKamehameha" || id == "dragonFist" ||
            id == "superEnergyBackflow" || id == "superKamehameha") { id = "ironReaver"; }
        return this.gogetaNativeMoveLabel.call(this,{moveId:id,characterId:"i"});
    };
    picker.gogetaNativeShowPicker = picker.showPicker;
    picker.showPicker = function(args) {
        var background = this._display_mc.background_mc;
        if (args.player.characterId != "go" && background.gogetaFrozen) {
            b.backgroundChildren(background,true);
            background.gogetaFrozen = false;
        }
        var result = this.gogetaNativeShowPicker.call(this,args);
        // The original background contains eight labels and no go label.
        // Stop a real frame, otherwise its initial playback cycles all eight.
        if (args.player.characterId == "go") {
            background.gotoAndStop("i");
            b.backgroundChildren(background,false);
            background.gogetaFrozen = true;
        }
        return result;
    };
    var status = g.viewPlayersStatus;
    status.gogetaNativeRefresh = status._refreshPlayerDisplay;
    status._refreshPlayerDisplay = function(args) {
        var nativeArgs = args;
        if (args.characterId == "go") {
            nativeArgs = {};
            for (var key in args) { nativeArgs[key] = args[key]; }
            nativeArgs.characterId = "i";
        }
        var result = this.gogetaNativeRefresh.call(this,nativeArgs);
        var portrait = this._playersClips[args.index].portrait_mc;
        if (args.characterId == "go") { b.showGogetaPortrait(portrait,32); }
        else { portrait.gogetaPortrait_mc.removeMovieClip(); }
        return result;
    };
    var minimap = g.viewMiniMap;
    minimap.gogetaNativeDisplay = minimap._displayNew;
    minimap._displayNew = function(args) {
        var safe = [];
        for (var index=0; index<args.players.length; index++) {
            safe[index] = {};
            for (var key in args.players[index]) { safe[index][key] = args.players[index][key]; }
            if (safe[index].characterId == "go") { safe[index].characterId = "i"; }
        }
        var result = this.gogetaNativeDisplay.call(this,{players:safe});
        for (var index=0; index<args.players.length; index++) {
            var clip = this._playersClips[index].character_mc;
            if (args.players[index].characterId == "go") { b.showGogetaPortrait(clip,16); }
            else { clip.gogetaPortrait_mc.removeMovieClip(); }
        }
        return result;
    };
    var roundView = g.viewRound;
    roundView.gogetaNativeStart = roundView.startRound;
    roundView.startRound = function(args) {
        if (args.background != "go") { return this.gogetaNativeStart.call(this,args); }
        return this.gogetaNativeStart.call(this,{roundSequence:args.roundSequence,background:"i"});
    };
    roundView.gogetaNativeCards = roundView._doMove_ShowCards;
    roundView._doMove_ShowCards = function(args) {
        var labels = args.move.cardsLabels;
        var safeMove = {};
        for (var key in args.move) { safeMove[key] = args.move[key]; }
        safeMove.cardsLabels = [];
        var gogetaIds = [];
        for (var index=0; index<labels.length; index++) {
            var label = labels[index];
            if (label.substr(0,2) == "go") {
                var upperId = label.substr(2);
                var id = upperId.charAt(0).toLowerCase()+upperId.substr(1);
                gogetaIds[index] = id;
                safeMove.cardsLabels[index] = picker._generateMoveLabelName({moveId:id,characterId:"go"});
            } else { safeMove.cardsLabels[index] = label; }
        }
        var result = this.gogetaNativeCards.call(this,{move:safeMove});
        for (var index=0; index<labels.length; index++) {
            var clip = this._cardsDisplay_mc["card_"+args.move.turnNum+"_player_"+index+"_mc"];
            var reveal = this._cardsDisplay_mc["card_"+index+"_fx_mc"];
            if (gogetaIds[index] != undefined) {
                b.decorateGogetaCard(picker,clip,gogetaIds[index]);
                b.decorateGogetaCard(picker,reveal,gogetaIds[index]);
            } else {
                b.clearGogetaCardArt(clip);
                b.clearGogetaCardArt(reveal);
            }
        }
        return result;
    };
};

// END SHARED GOGETA DISPLAY
b.addCompatible = function(moveId) {
    var description = g.movieMediator._movesDescriptions[moveId];
    var move = g.movieMediator._allMoves[moveId];
    if (move == undefined || move.compatibleCharacters == undefined) { return false; }
    if (description != undefined && description.compatibleCharacters != undefined &&
        !this.arrayHas(description.compatibleCharacters,"go")) { description.compatibleCharacters.push("go"); }
    if (!this.arrayHas(move.compatibleCharacters,"go")) { move.compatibleCharacters.push("go"); }
    return true;
};
b.addGogetaMove = function(id, name, energy, damage, area) {
    var description = {
        id:id,
        name:name,
        target:"enemy",
        type:"action",
        advanced:false,
        compatibleCharacters:["go"],
        depthMod:1,
        userImpact:{locDiff:[0,0],effectArea:[[0,0,0],[0,1,0],[0,0,0]],lifeDiff:0,energyDiff:energy,protection:0},
        enemyImpact:{locDiff:[0,0],effectArea:area,lifeDiff:damage,energyDiff:0,protection:0},
        order:0,fresh:false
    };
    g.movieMediator._movesDescriptions[id] = description;
    // MoveData and CharacterData are data-only containers in the original
    // game. FFDec's replacement compiler cannot reliably instantiate a
    // constructor stored in a local variable at runtime, so use the exact
    // constructed data shape instead of rebuilding all original moves.
    g.movieMediator._allMoves[id] = description;
};
b.installGogeta = function() {
    if (this.gogetaInstalled) { return true; }
    if (g.movieMediator == undefined || g.movieMediator._allMoves == undefined ||
        g.movieMediator._characters == undefined || g.movieMediator._movesDescriptions == undefined ||
        g.movieMediator._charactersDescriptions == undefined) { return false; }
    try {
        this.addGogetaMove("bigBangKamehameha", "빅뱅 애네르기파", -50, -40, [[0,0,0],[0,1,0],[1,1,1]]);
        this.addGogetaMove("dragonFist", "용권", -60, -70, [[0,0,0],[1,1,1],[0,0,0]]);
        this.addGogetaMove("superEnergyBackflow", "초 에너지 역류", -25, -25, [[1,1,1],[1,1,1],[1,1,1]]);
        this.addGogetaMove("superKamehameha", "초 에네르기파", -20, -35, [[0,0,0],[1,1,1],[0,0,0]]);

        var shared = ["guard","energyUp","moveLeft","moveRight","moveUp","moveDown",
                      "perfectGuard","heal","kikyosRevenge","doubleRight","doubleLeft","summonShippo"];
        for (var sharedIndex=0; sharedIndex<shared.length; sharedIndex++) { this.addCompatible(shared[sharedIndex]); }

        var regular = {};
        var regularIds = ["guard","energyUp","moveLeft","moveRight","moveUp","moveDown",
                          "bigBangKamehameha","dragonFist","superEnergyBackflow","superKamehameha"];
        for (var moveIndex=0; moveIndex<regularIds.length; moveIndex++) {
            regular[regularIds[moveIndex]] = g.movieMediator._allMoves[regularIds[moveIndex]];
        }
        g.movieMediator._charactersDescriptions.go = {name:"Gogeta",level:8,fightList:[]};
        g.movieMediator._characters.go = {
            name:"Gogeta",level:8,moves:regular,advancedMoves:{},id:"go",
            maxHealth:100,maxEnergy:100,locked:false,defeated:false
        };
        if (g.viewRoundPlayers != undefined && g.viewRoundPlayers._characterIdToLinkageIdKey != undefined) {
            g.viewRoundPlayers._characterIdToLinkageIdKey.go = {figure:"goMoves",fxTop:"goFxTop",fxBottom:"goFxBottom"};
        }
        this.installGogetaDisplay();
        this.gogetaInstalled = true;
        return true;
    } catch (error) { return false; }
};
b.configure = function(seat) { this.seat = Number(seat); return this.installGogeta(); };
b.chooseGogeta = function() {
    if (this.phase != "selecting" || !this.installGogeta()) { return false; }
    var character = g.movieMediator._characters.go;
    if (character == undefined) { return false; }
    g.movieMediator.userPickedCharacter({character:character});
    return true;
};
b.gogetaState = function() {
    var moveIds = ["bigBangKamehameha","dragonFist","superEnergyBackflow","superKamehameha"];
    var moves = {};
    for (var moveIndex=0; moveIndex<moveIds.length; moveIndex++) {
        var id = moveIds[moveIndex];
        var move = g.movieMediator._allMoves[id];
        moves[id] = {
            energy:move.userImpact.energyDiff,
            damage:move.enemyImpact.lifeDiff,
            area:move.enemyImpact.effectArea
        };
    }
    var regularMoves = [];
    for (var regularId in g.movieMediator._characters.go.moves) { regularMoves.push(regularId); }
    return {
        installed:this.installGogeta(),phase:this.phase,
        character:g.movieMediator._characters.go != undefined,
        move:g.movieMediator._allMoves.bigBangKamehameha != undefined,
        moves:moves,
        regularMoves:regularMoves,
        linkage:g.viewRoundPlayers._characterIdToLinkageIdKey.go
    };
};
b.select = function() {
    if (this.phase != "selecting") { return false; }
    g.movieMediator._pickUserCharacter();
    return true;
};
b.reset = function() {
    clearInterval(this.timer);
    this.phase = "selecting";
    this.round = 0;
    g.viewPickMoves.hidePicker();
    g.viewPickMoves.closeHelp();
    g.viewRound.hide();
    g.viewBattleLoading.hide();
    g.viewMatchResult.hide();
    g.viewVersus.hide();
    g.gameManager._playersMoves = [[],[]];
    g.gameManager._players = [{},{}];
    g.gameManager._roundSummary = {};
    g.gameManager._roundsCount = 0;
    g.movieMediator._players = [{},{}];
    g.movieMediator._pickUserCharacter();
    return true;
};
b.start = function(match, idsText, cardsText, dedicatedText) {
    if (!this.installGogeta()) { return false; }
    var ids = idsText.split(",");
    var cards = cardsText == "" ? [] : cardsText.split(",");
    var dedicated = dedicatedText == undefined ? ["",""] : dedicatedText.split(",");
    this.match = Number(match);
    this.round = 1;
    this.phase = "loading";
    // Match the original userDoneWithVersus audio transition.
    g.soundManager.stop({id:"themeSong"});
    g.soundManager.stop({id:"youDie"});
    g.viewPickCharacter.hidePickCharacter();
    g.viewVersus.hide();
    g.viewRound.hide();
    g.viewPickMoves.hidePicker();
    g.Prefs.easyWin = false;
    var players = [];
    for (var i=0; i<2; i++) {
        var bonus = {};
        for (var j=0; j<cards.length; j++) { bonus[cards[j]] = g.movieMediator._allMoves[cards[j]]; }
        if (dedicated[i] != "" && dedicated[i] != undefined) { bonus[dedicated[i]] = g.movieMediator._allMoves[dedicated[i]]; }
        players[i] = g.movieMediator._createPlayer({character:g.movieMediator._characters[ids[i]],type:i,advancedMoves:bonus});
    }
    g.pickMovesManager._humanPlayerIndex = this.seat;
    g.pickMovesManager._computerPlayerIndex = 1-this.seat;
    g.movieMediator._players = players;
    g.battleLoadManager.load({ids:ids});
    g.gameManager.newMatch({players:players});
    this.loadStarted = getTimer();
    clearInterval(this.timer);
    this.timer = setInterval(this, "pollLoaded", 100);
    return true;
};
b.pollLoaded = function() {
    if (g.battleLoadManager.getPercentLoaded() == 100) {
        clearInterval(this.timer);
        this.emit("loaded", {match:this.match});
    } else if (getTimer()-this.loadStarted > 45000) {
        clearInterval(this.timer);
        this.emit("fault", {message:"캐릭터 리소스를 불러오지 못했습니다."});
    }
};
b.next = function(match, round) {
    if (Number(match) != this.match || !(this.phase == "loading" || this.phase == "waiting")) { return false; }
    this.round = Number(round);
    this.phase = "picking";
    g.gameManager._roundsCount = this.round;
    g.gameManager.pvpOriginalRequest.call(g.gameManager);
    return true;
};
b.play = function(match, round, hand0Text, hand1Text) {
    if (Number(match) != this.match || Number(round) != this.round || this.phase != "submitted") { return false; }
    var hands = [hand0Text.split(","),hand1Text.split(",")];
    var moves = [[],[]];
    for (var i=0; i<2; i++) {
        for (var j=0; j<3; j++) { moves[i][j] = g.gameManager._players[i].moves[hands[i][j]]; }
        g.gameManager._players[i].roundMoves = moves[i];
    }
    this.phase = "playing";
    g.viewPickMoves.hidePicker();
    g.gameManager.newMoves({moves:moves});
    return true;
};
b.retry = function(match, round) {
    if (Number(match) != this.match || Number(round) != this.round || this.phase != "submitted") { return false; }
    this.phase = "picking";
    g.gameManager.pvpOriginalRequest.call(g.gameManager);
    return true;
};
g.movieMediator.pvpOriginalPickUserCharacter = g.movieMediator._pickUserCharacter;
g.movieMediator._pickUserCharacter = function() {
    var result = this.pvpOriginalPickUserCharacter.call(this);
    b.emit("picking",{});
    return result;
};
g.movieMediator.userPickedCharacter = function(args) {
    if (b.phase != "selecting") { return; }
    g.viewPickCharacter.hidePickCharacter();
    b.emit("character", {character:args.character.id});
};
g.pickMovesManager.donePickingMoves = function(args) {
    if (b.phase != "picking") { return; }
    var ids = [];
    for (var i=0; i<3; i++) { if (args.moves[i].id == undefined) { return; } ids[i] = args.moves[i].id; }
    b.phase = "submitted";
    g.viewPickMoves.hidePicker();
    b.emit("moves", {match:b.match,round:b.round,moves:ids});
};
g.gameManager.pvpOriginalRequest = g.gameManager._requestMoves;
g.gameManager._requestMoves = function() {
    if (b.phase == "loading") { return; }
    b.phase = "waiting";
    g.viewRound.hide();
    b.emit("finished", {match:b.match,round:b.round});
};
g.gameManager.pvpOriginalBegin = g.gameManager._beginRound;
g.gameManager._beginRound = function(args) {
    this.pvpOriginalBegin.call(this,args);
    var summary = this._roundSummary;
    var state = [];
    for (var i=0; i<2; i++) { var p = this._players[i]; state[i] = {life:p.life,energy:p.energy,loc:[p.loc[0],p.loc[1]]}; }
    var winner = summary.matchResult == "win" ? Number(summary.winner) : null;
    b.emit("resolved", {match:b.match,round:b.round,players:state,result:summary.matchResult,winner:winner});
};
g.gameManager._matchDone = function(args) {
    this.em.broadcast({event:"matchDone",args:{matchResult:args.matchResult}});
};
g.movieMediator.matchDone = function(args) {
    b.phase = "result";
    b.emit("finished", {match:b.match,round:b.round});
};
g.movieMediator.userDoneWithMatchResult = function() { b.emit("rematch",{}); };
// Add one native card clip for five common cards plus a character card.
// Keep the original five-card layout whenever at most five cards are present.
var picker = g.viewPickMoves;
var row = picker._moveSelectorClips[2];
var origins = [];
for (var slotIndex=0; slotIndex<5; slotIndex++) {
    origins[slotIndex] = {x:row[slotIndex]._x,y:row[slotIndex]._y,xscale:row[slotIndex]._xscale,yscale:row[slotIndex]._yscale};
}
row[4].duplicateMovieClip("card_25_pvp_mc",12000);
row[5] = picker._display_mc.card_25_pvp_mc;
// Keep the additional card in the card layer, below native dialog overlays.
row[5].swapDepths(row[4].getDepth()+1);
picker._registerInputReceptor({obj:row[5]});
picker.pvpOrigins = origins;
picker.pvpOriginalShowMoves = picker._showMoves;
picker._showMoves = function() {
    var count = 0;
    for (var id in this._playerMoves) { if (this._playerMoves[id].advanced) { count++; } }
    var clips = this._moveSelectorClips[2];
    var saved = this.pvpOrigins;
    var step = (saved[4].x-saved[0].x)/4;
    var ratio = count > 5 ? 5/6 : 1;
    for (var i=0; i<6; i++) {
        var origin = i < 5 ? saved[i] : saved[4];
        clips[i]._visible = i < count;
        clips[i]._x = count > 5 ? saved[0].x+i*step*ratio : origin.x;
        clips[i]._y = origin.y;
        clips[i]._xscale = origin.xscale*ratio;
        clips[i]._yscale = origin.yscale*ratio;
    }
    this.pvpOriginalShowMoves.call(this);
    b.decorateGogetaMoveCards(this);
};
picker.pvpOriginalShowSelectedMoves = picker._showSelectedMoves;
picker._showSelectedMoves = function() {
    this.pvpOriginalShowSelectedMoves.call(this);
    b.decorateGogetaSelectedCards(this);
};
ei.addCallback("pvpConfigure",b,b.configure);
ei.addCallback("pvpSelect",b,b.select);
ei.addCallback("pvpStart",b,b.start);
ei.addCallback("pvpPlay",b,b.play);
ei.addCallback("pvpNext",b,b.next);
ei.addCallback("pvpReset",b,b.reset);
ei.addCallback("pvpRetry",b,b.retry);
ei.addCallback("pvpChooseGogeta",b,b.chooseGogeta);
ei.addCallback("pvpGogetaState",b,b.gogetaState);
b.emit("ready",{});
