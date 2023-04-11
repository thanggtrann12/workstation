angular.module("App", ["ngSanitize"]);
let app = angular.module("App");

app.controller("AppController", function($scope, $http) {
    const SCC_TRACE_CONTENT_MAX_LINES = 200;
    $scope.lockStatus = "";
    $scope.powerStatus = "";
    $scope.updateStatus = "";
    $scope.updateError = "";
    $scope.sccLines = [];

    $scope.userName = "";
    $scope.voltageInput = "";
    $scope.voltageOutput = "0";
    $scope.currentOutput = "0";
    $scope.sccCommandStr = "";

    $scope.terminal = new Terminal({
        cursorBlink: true,
        macOptionIsMeta: true,
        scrollback: 200
    });

    $scope.terminal.open($("#terminalId")[0]);

    $scope.socket = io("http://" + location.host);

    $("#btnSubmit").click((e) => {
        const content = $("#textValue").val();
        $("#textValue").val('');
        $scope.socket.emit("appInput", {"input": content});
        $('#textValue').focus();
    });

    $scope.terminal.on("key", async function(key_, event_) {
        let content = key_;

        // Ctrl + c
        if (key_.charCodeAt(0) === 0x03 && $scope.terminal.hasSelection()) {
            await navigator.clipboard.writeText($scope.terminal.getSelection());
            return;
        } // Ctrl + v
        else if (key_.charCodeAt(0) === 0x16) {
            // not working for default firefox - need to change permission
            // https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/readText#browser_compatibility
            content = await navigator.clipboard.readText();
        }
        $scope.$apply(function() {
            $scope.socket.emit("appInput", {"input":content});
        }); 
    });

    $scope.socket.on("connect", function() {
        $scope.$apply(function() {
            $scope.sccLines = [];
        });
    });

    $scope.socket.on("appContent", function(data_) {
        $scope.$apply(function() {
            $scope.terminal.write(data_["data"]);
        });
    });

    $scope.socket.on("powerValue", function(data_) {
        $scope.$apply(function() {
            $scope.currentOutput = data_.current;
            $scope.voltageOutput = data_.voltage;
        });
    });

    $scope.socket.on("lockStatus", function(data_) {
        $scope.$apply(function() {
            let lockUser = data_.data;
            if ("" != lockUser) {
                $scope.lockStatus = "System is being locked by " + lockUser;
            }
            else {
                $scope.lockStatus = "";
            }
        });
    });

    $scope.socket.on("updateStatus", function(data_) {
        $scope.$apply(function() {
            $scope.updateStatus = data_.data;
        });
    });

    $scope.socket.on("message", function(message_) {
        let bIsAtBottom = true;
        let traceArea = $("#sccTraceAreaId")[0];

        if (traceArea.scrollHeight > (traceArea.clientHeight + traceArea.scrollTop)) {
            bIsAtBottom = false;
        }

        $scope.$apply(function() {
            let lines = $scope.sccLines.concat(message_.split("\n"));
            $scope.sccLines = lines;
        });

        if (bIsAtBottom) {
            traceArea.scrollTop = traceArea.scrollHeight - traceArea.clientHeight;
        }
    });

    $scope.UploadFiles = function() {
        $scope.updateError = "";
        let url = "http://" + location.host + "/Upload/";
        let formData = new FormData($("#uploadFormId")[0]);
        $http({
            method: "POST",
            url: url,
            data: formData,
            headers: {
                "Content-Type": undefined
            }
        }).then(function(resp) {
            let errorStr = resp.data.error;
            if (null != errorStr) {
                $scope.updateError = errorStr;
            }
        });
    };

    $scope.Sleep = function(event) {
        let url = "http://" + location.host + "/Sleep/";
        $http.get(url).then(function(resp) {
        });
    };

    $scope.Reset = function(event) {
        let url = "http://" + location.host + "/Reset/";
        $http.get(url).then(function(resp) {
        });
    };

    $scope.ExportSccTrace = function() {
        let blob = new Blob([$scope.sccLines.join("\n")], {type:"text/plain"});
        let downloader = $("#downloaderId")[0];
        downloader.href=window.URL.createObjectURL(blob);
        downloader.download = "output.pro";
        downloader.click();
    };
    
    $scope.ClearSccTrace = function() {
        $scope.sccLines = [];
    };
    
    $scope.ExportTerminalLog = function() {
        const term = $scope.terminal;
        term.selectAll();

        let blob = new Blob([term.getSelection().trim()], {type:"text/plain"});
        let downloader = $("#downloaderId")[0];
        downloader.href = window.URL.createObjectURL(blob);
        downloader.download = `${new Date().toISOString()}-log.txt`;
        downloader.click();
    }

    $scope.ClearTerminalLog = function() {
        $scope.terminal.clear();
    }

    $scope.ToggleMore = function() {
        $(".fa-plus").toggleClass('fa-minus')
        
        if ($('.cmtDiv').is(':visible')) {
            $('.cmtDiv').fadeOut();
        } else {
            $('.cmtDiv').fadeIn();
            $('#textValue').focus();
        }

    }

    $scope.paraTable = {};
    $scope.sepRegex = /((^|\W)+[^ ]*)/g;
    $scope.state = 0;
    $scope.suggestionList = [];
    $scope.inSelection = false;
    $scope.commandTable = {
        root: new Trie({}),
        enum: {},
    };

    
    $scope.updateLastCommand = (command) => {
      let commandList = $scope.sccCommandStr.match($scope.sepRegex);
      commandList.pop();
      commandList.push(command);
      commandList = commandList.map((ele) => ele.trim());
      $scope.sccCommandStr = (commandList.join(' '));
    };

    $scope.LoadParaTable = async () => {
        let data = await $.get('http://' + location.host + '/GetCommandSet/');

        // Insert base command
        for (let cmd in data['root']) {
            $scope.commandTable['root'].insert(cmd);
        }

        // Insert enum name value
        for (let name in data['enum']) {
            $scope.commandTable['enum'][name] = new Trie({});
            for (let value of data['enum'][name]) {
                $scope.commandTable['enum'][name].insert(value);
            }
        }

        // Update parameter table
        $scope.paraTable = data['root'];
    };

    $scope.parseInput = () => {
      let nameList = $scope.sccCommandStr.match($scope.sepRegex);
      let baseCommand = nameList[0];
      let latestName = nameList.at(-1).trim();
      let pos = nameList.length;
      return [baseCommand, latestName, pos];
    };

    $scope.DoAutoComplete = function(event) {
        if (9 == event.keyCode) {
            event.preventDefault();
            // get suggestion
            if (!$scope.inSelection) {
                $scope.suggestionList = [];
                let [baseCommand, name, pos] = $scope.parseInput();

                if (pos === 1) {
                    $scope.suggestionList = $scope.commandTable['root'].find(name);
                } else if ($scope.paraTable[baseCommand]) {
                    // pos - 2 is to compensate the base command and zero-index array
                    let enumName = $scope.paraTable[baseCommand][pos - 2];
                    if (enumName) {
                        $scope.suggestionList = $scope.commandTable['enum'][enumName].find(name);
                    }
                }
                $scope.inSelection = true;
            }

            // cycle through suggestion
            if ($scope.suggestionList.length != 0) {
                $scope.updateLastCommand($scope.suggestionList[$scope.state]);
                $scope.state = ($scope.state + 1) % $scope.suggestionList.length;
            }
        } else {
            $scope.inSelection = false;
            $scope.state = 0;
        }

        if (13 == event.keyCode) {
            let url = "http://" + location.host + "/RunCommand/";
            $http({
                method: "POST",
                url: url,
                data: $scope.sccCommandStr,
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(function(resp) {
                $scope.sccCommandStr = "";
            });
        }
    };

    $scope.Lock = function(event) {
        $scope.userName = $scope.userName.trim();
        if ("" != $scope.userName) {
            let url = "http://" + location.host + "/Lock/";
            $http({
                method: "POST",
                url: url,
                data: $scope.userName,
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(function(resp) {

            });
        }
    };

    $scope.Unlock = function(event) {
        let url = "http://" + location.host + "/Unlock/";
        $http.get(url).then(function(resp) {
            $scope.lockStatus = "";
        });
    };

    $scope.SetVoltage = function(event) {
        $scope.voltageInput = $scope.voltageInput.trim();
        if ("" != $scope.voltageInput) {
            let url = "http://" + location.host + "/SetVoltage/";
            $http({
                method: "POST",
                url: url,
                data: $scope.voltageInput,
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(function(resp) {
                $scope.powerStatus = resp.data.result;
            });
        }
    };

    $scope.PowerOff = function(event) {
        let url = "http://" + location.host + "/SetPower/off/";
        $http.get(url).then(function(resp) {
            $scope.powerStatus = resp.data.result;
        });
    };

    $scope.PowerOn = function(event) {
        let url = "http://" + location.host + "/SetPower/on/";
        $http.get(url).then(function(resp) {
            $scope.powerStatus = resp.data.result;
        });
    };

    $scope.ResizeTerminalArea = function() {
        let terminal = $("#terminalId")[0];
        let nCols = Math.floor(terminal.clientWidth / $scope.terminal._core._renderCoordinator._renderer.dimensions.actualCellWidth);
        let nRows = Math.floor(terminal.clientHeight / $scope.terminal._core._renderCoordinator._renderer.dimensions.actualCellHeight);
        $scope.terminal.resize(nCols, nRows);
    }

    $scope.ResizeTerminalArea();
    $(window).bind("resize", $scope.ResizeTerminalArea);
});
