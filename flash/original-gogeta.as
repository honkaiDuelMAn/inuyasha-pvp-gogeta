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
b.gogetaCardImages = {
    bigBangKamehameha:true,
    dragonFist:true,
    superEnergyBackflow:true,
    superKamehameha:true
};
b.clearGogetaCardArt = function(clip) {
    if (clip != undefined && clip.gogetaArt_mc != undefined) { clip.gogetaArt_mc.removeMovieClip(); }
};
b.decorateGogetaCard = function(view, clip, moveId) {
    if (clip == undefined) { return; }
    this.clearGogetaCardArt(clip);
    if (moveId == undefined || moveId == null || moveId == "") { return; }
    if (this.gogetaCardImages[moveId]) {
        var art = clip.createEmptyMovieClip("gogetaArt_mc",1000);
        art._x = 0;
        art._y = 0;
        art.enabled = false;
        art.useHandCursor = false;
        art.loadMovie("gogeta/cards/"+moveId+".png");
        return;
    }
    var donorLabel = view._generateMoveLabelName({moveId:moveId,characterId:"i"});
    clip.gotoAndStop(donorLabel);
};
b.decorateGogetaMoveCards = function(view) {
    if (view == undefined || view._player == undefined || view._player.characterId != "go") { return; }
    for (var rowIndex=0; rowIndex<view._moveSelectorClips.length; rowIndex++) {
        var moveRow = view._moveSelectorClips[rowIndex];
        for (var column=0; column<moveRow.length; column++) {
            var moveClip = moveRow[column];
            this.decorateGogetaCard(view,moveClip,moveClip.moveId);
        }
    }
};
b.decorateGogetaSelectedCards = function(view) {
    if (view == undefined || view._player == undefined || view._player.characterId != "go") { return; }
    for (var index=0; index<view._selectedMovesClips.length; index++) {
        var selectedMove = view._selectedMoves[index];
        this.decorateGogetaCard(view,view._selectedMovesClips[index],selectedMove == 0 ? null : selectedMove.id);
    }
};
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
