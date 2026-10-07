stop();
var gameRoot = _level0;
var g = gameRoot.originalgame;
var b = gameRoot.originalGogetaBridge = {installed:false};
var ei = flash.external.ExternalInterface;
b.emit = function(kind, data) { ei.call("originalGogetaEvent", kind, data); };
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
    g.movieMediator._allMoves[id] = description;
};
b.install = function() {
    if (this.installed) { return true; }
    if (g == undefined || g.movieMediator == undefined || g.userStatsManager == undefined ||
        g.movieMediator._allMoves == undefined || g.movieMediator._characters == undefined ||
        g.movieMediator._movesDescriptions == undefined || g.movieMediator._charactersDescriptions == undefined ||
        g.userStatsManager._enemyLevelKey == undefined) { return false; }
    try {
        this.addGogetaMove("bigBangKamehameha", "빅뱅 애네르기파", -50, -40, [[0,0,0],[0,1,0],[1,1,1]]);
        this.addGogetaMove("dragonFist", "용권", -60, -70, [[0,0,0],[1,1,1],[0,0,0]]);
        this.addGogetaMove("superEnergyBackflow", "초 에너지 역류", -25, -25, [[1,1,1],[1,1,1],[1,1,1]]);
        this.addGogetaMove("superKamehameha", "초 에네르기파", -20, -35, [[0,0,0],[1,1,1],[0,0,0]]);

        var shared = ["guard","energyUp","moveLeft","moveRight","moveUp","moveDown",
                      "perfectGuard","heal","kikyosRevenge","doubleRight","doubleLeft","summonShippo"];
        for (var sharedIndex=0; sharedIndex<shared.length; sharedIndex++) { this.addCompatible(shared[sharedIndex]); }

        var found = g.movieMediator._findCharacterMoves({id:"go"});
        g.movieMediator._charactersDescriptions.go = {name:"Gogeta",level:8,fightList:["sa","ko","ka","s","n"]};
        g.movieMediator._characters.go = {
            name:"Gogeta",level:8,moves:found.regular,advancedMoves:found.advanced,id:"go",
            maxHealth:100,maxEnergy:100,locked:false,defeated:false
        };
        g.userStatsManager._enemyLevelKey.go = ["sa","ko","ka","s","n"];
        if (g.viewRoundPlayers != undefined && g.viewRoundPlayers._characterIdToLinkageIdKey != undefined) {
            g.viewRoundPlayers._characterIdToLinkageIdKey.go = {figure:"goMoves",fxTop:"goFxTop",fxBottom:"goFxBottom"};
        }

        var versusView = g.viewVersus;
        if (versusView != undefined && versusView.originalGogetaRedraw == undefined) {
            versusView.originalGogetaRedraw = versusView._redraw;
            versusView._redraw = function(args) {
                if (args.playerA == "go") {
                    var gogetaResult = this.originalGogetaRedraw.call(this,{
                        playerA:"i",playerB:args.playerB,enemies:args.enemies,userChoice:args.userChoice
                    });
                    if (this._display_mc.giantA_mc != undefined) { this._display_mc.giantA_mc._visible = false; }
                    if (this._display_mc.kanjiA_mc != undefined) { this._display_mc.kanjiA_mc._visible = false; }
                    if (this._display_mc.portraitA_mc != undefined) { this._display_mc.portraitA_mc._visible = false; }
                    return gogetaResult;
                }
                var originalResult = this.originalGogetaRedraw.call(this,args);
                if (this._display_mc.giantA_mc != undefined) { this._display_mc.giantA_mc._visible = true; }
                if (this._display_mc.kanjiA_mc != undefined) { this._display_mc.kanjiA_mc._visible = true; }
                if (this._display_mc.portraitA_mc != undefined) { this._display_mc.portraitA_mc._visible = true; }
                return originalResult;
            };
        }

        var picker = g.viewPickMoves;
        if (picker != undefined && picker.originalGogetaShowMoves == undefined) {
            picker.originalGogetaShowMoves = picker._showMoves;
            picker._showMoves = function() {
                this.originalGogetaShowMoves.call(this);
                b.decorateGogetaMoveCards(this);
            };
            picker.originalGogetaShowSelectedMoves = picker._showSelectedMoves;
            picker._showSelectedMoves = function() {
                this.originalGogetaShowSelectedMoves.call(this);
                b.decorateGogetaSelectedCards(this);
            };
        }

        if (g.movieMediator.originalGogetaPickUserCharacter == undefined) {
            g.movieMediator.originalGogetaPickUserCharacter = g.movieMediator._pickUserCharacter;
            g.movieMediator._pickUserCharacter = function() {
                var result = this.originalGogetaPickUserCharacter.call(this);
                b.emit("picking",{});
                return result;
            };
        }
        if (g.movieMediator.originalGogetaUserPickedCharacter == undefined) {
            g.movieMediator.originalGogetaUserPickedCharacter = g.movieMediator.userPickedCharacter;
            g.movieMediator.userPickedCharacter = function(args) {
                b.emit("selected",{character:args.character.id});
                return this.originalGogetaUserPickedCharacter.call(this,args);
            };
        }
        if (g.movieMediator.originalGogetaShowVersus == undefined) {
            g.movieMediator.originalGogetaShowVersus = g.movieMediator._showVersus;
            g.movieMediator._showVersus = function(args) {
                var result = this.originalGogetaShowVersus.call(this,args);
                b.emit("versus",{characters:[args.userId,args.enemyId]});
                return result;
            };
        }
        if (g.movieMediator.originalGogetaDoneWithVersus == undefined) {
            g.movieMediator.originalGogetaDoneWithVersus = g.movieMediator.userDoneWithVersus;
            g.movieMediator.userDoneWithVersus = function(args) {
                var userId = this._userStatsManager.getStats().id;
                var result = this.originalGogetaDoneWithVersus.call(this,args);
                b.emit("battle",{characters:[userId,args.enemyId]});
                return result;
            };
        }
        if (g.movieMediator.originalGogetaMatchDone == undefined) {
            g.movieMediator.originalGogetaMatchDone = g.movieMediator.matchDone;
            g.movieMediator.matchDone = function(args) {
                var result = this.originalGogetaMatchDone.call(this,args);
                b.emit("result",{result:args.matchResult});
                return result;
            };
        }
        this.installGogetaDisplay();
        this.installed = true;
        return true;
    } catch (error) {
        this.lastError = String(error);
        return false;
    }
};
b.chooseGogeta = function() {
    if (!this.install()) { return false; }
    var character = g.movieMediator._characters.go;
    if (character == undefined) { return false; }
    g.movieMediator.userPickedCharacter({character:character});
    return true;
};
b.state = function() {
    if (!this.install()) { return {installed:false,error:this.lastError}; }
    var moveIds = ["bigBangKamehameha","dragonFist","superEnergyBackflow","superKamehameha"];
    var moves = {};
    for (var moveIndex=0; moveIndex<moveIds.length; moveIndex++) {
        var id = moveIds[moveIndex];
        var move = g.movieMediator._allMoves[id];
        moves[id] = {energy:move.userImpact.energyDiff,damage:move.enemyImpact.lifeDiff,area:move.enemyImpact.effectArea};
    }
    var regularMoves = [];
    var advancedMoves = [];
    var summons = [];
    for (var regularId in g.movieMediator._characters.go.moves) { regularMoves.push(regularId); }
    for (var advancedId in g.movieMediator._characters.go.advancedMoves) {
        advancedMoves.push(advancedId);
        if (advancedId.indexOf("summon") == 0) { summons.push(advancedId); }
    }
    var secretSword = g.movieMediator._allMoves.secretSword;
    var poisonPowder = g.movieMediator._allMoves.poisonPowder;
    return {
        installed:true,
        character:g.movieMediator._characters.go != undefined,
        moves:moves,
        regularMoves:regularMoves,
        advancedMoves:advancedMoves,
        summons:summons,
        enemyOrder:g.userStatsManager._enemyLevelKey.go,
        linkage:g.viewRoundPlayers._characterIdToLinkageIdKey.go,
        sango:{secretSword:{energy:secretSword.userImpact.energyDiff,damage:secretSword.enemyImpact.lifeDiff},poisonPowder:{energy:poisonPowder.userImpact.energyDiff,damage:poisonPowder.enemyImpact.lifeDiff}}
    };
};
ei.addCallback("originalChooseGogeta",b,b.chooseGogeta);
ei.addCallback("originalGogetaState",b,b.state);
if (b.install()) {
    b.emit("ready",b.state());
    b.emit("picking",{});
} else {
    b.emit("fault",{message:"오지터 원본 모드 데이터를 설치하지 못했습니다.",error:b.lastError});
}
