let stopFlag = false // Flag to indicate if the timer should stop

const E_OK = true
const E_NOK = false

async function timer(duration, condition, transition, expired, log) {
	let temp_dur = duration
	while (temp_dur > 0 && !stopFlag) {
		temp_dur -= 1
		if (!condition) {
			transition()
			break
		}
		await delay(1000)
	}
	if (condition) expired()
	log
}

function delay(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms))
}

let time_execute = 0

async function executeTest(
	time,
	action,
	duration,
	condition,
	transition,
	expired,
) {
	let temp_time = time
	stopFlag = false // Reset stop flag
	action
	while (temp_time > 0 && !stopFlag) {
		time_execute = time - temp_time
		$("#status").text("Current test time: " + time_execute)
		await timer(duration, condition, transition, expired)
		console.log("time: ", temp_time)
		temp_time -= 1
	}
}

function stopExecution() {
	stopFlag = true
}
