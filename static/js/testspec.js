let testTime = 0
// const TIMEOUT_FOR_TEST = 5
const DEFAULT_TEST_TIME = 5
const TIMEOUT_FOR_TEST = 5 * 60
async function standby_test() {
	await executeTest(
		testTime == 0 ? DEFAULT_TEST_TIME : testTime,
		removeACCIGN(),
		TIMEOUT_FOR_TEST,
		getTargetStatus(),
		async () => {
			updateTtfiData("[PASSED]")
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			saveLog("STANDBY", "PASSED", time_execute)
		},
		async () => {
			updateTtfiData("[FAILED] Timer expired")
			updateTtfiData("[SET POWER DOWN]")
			setTargetPowerDown()
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			updateTtfiData("[SET POWER ON]")
			setTargetPowerUp()
		},
		saveLog("SHUTDOWN", "FAILED", time_execute),
	)
}

async function shutdown_test() {
	await executeTest(
		testTime == 0 ? DEFAULT_TEST_TIME : testTime,
		removeACCIGN(),
		TIMEOUT_FOR_TEST,
		getTargetStatus(),
		() => {
			updateTtfiData("[PASSED]")
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			saveLog("SHUTDOWN", "PASSED", time_execute)
		},
		async () => {
			updateTtfiData("[FAILED] Timer expired")
			updateTtfiData("[SET POWER DOWN]")
			await setTargetPowerDown()
			updateTtfiData("[PLUG ACC+IGN]")
			await setTargetWakeup()
			updateTtfiData("[SET POWER ON]")
			await setTargetPowerUp()
		},
		saveLog("SHUTDOWN", "FAILED", time_execute),
	)
}

function setTestTime() {
	testTime = parseInt($("#test_time").val())
	console.log(testTime)
}
function removeACCIGN() {
	$("#acc_button, #acc_label, #ign_button, #ign_label").css("color", "red")
	socket.emit("remove_accign")
}
async function setTargetWakeup() {
	$("#acc_button, #acc_label, #ign_button, #ign_label").css("color", "#A6E22E")
	socket.emit("reconnect_accign")
}

function cancleTest() {
	stopExecution()
}
