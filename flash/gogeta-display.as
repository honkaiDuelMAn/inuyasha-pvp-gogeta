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
