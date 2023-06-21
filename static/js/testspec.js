let testTime = 0
const TIMEOUT_FOR_TEST = 5
const DEFAULT_TEST_TIME = 5
// const TIMEOUT_FOR_STANDBY = 5 * 60 * 1000
function standby_test() {
	executeTest(
		testTime == 0 ? DEFAULT_TEST_TIME : testTime,
		TIMEOUT_FOR_TEST,
		getTargetStatus(),
		() => {
			updateTtfiData("[PASSED]")
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			saveLog("STANDBY", "PASSED", time_execute)
		},
		() => {
			updateTtfiData("[FAILED]")
			updateTtfiData("[SET POWER DOWN]")
			setTargetPowerDown()
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			updateTtfiData("[SET POWER ON]")
			setTargetPowerUp()
			saveLog("STANDBY", "FAILED", time_execute)
		},
	)
}

function shutdown_test() {
	executeTest(
		testTime == 0 ? DEFAULT_TEST_TIME : testTime,
		TIMEOUT_FOR_TEST,
		getTargetStatus(),
		() => {
			updateTtfiData("[PASSED]")
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			saveLog("SHUTDOWN", "PASSED", time_execute)
		},
		() => {
			updateTtfiData("[FAILED]")
			updateTtfiData("[SET POWER DOWN]")
			setTargetPowerDown()
			updateTtfiData("[PLUG ACC+IGN]")
			setTargetWakeup()
			updateTtfiData("[SET POWER ON]")
			setTargetPowerUp()
			saveLog("SHUTDOWN", "FAILED", time_execute)
		},
	)
}

function setTestTime() {
	testTime = parseInt($("#test_time").val())
	console.log(testTime)
}
