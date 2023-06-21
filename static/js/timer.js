const E_OK = true
const E_NOK = false
async function timer(durantion, condition, transition, expired) {
	let temp_dur = durantion
	while (temp_dur > 0) {
		console.log("timer is running", temp_dur)
		temp_dur -= 1
		if (condition) {
			transition()
			break
		}
		await delay(1000)
	}
	if (!condition) expired()
}

function delay(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms))
}
let time_execute = 0
async function executeTest(time, durantion, condition, transition, expired) {
	let temp_time = time
	while (temp_time > 0) {
		var checkbox = document.getElementById("record_scc")
		checkbox.checked = true
		isRecording = true
		await timer(durantion, condition, transition, expired)
		console.log("time: ", temp_time)
		temp_time -= 1
		time_execute = time - temp_time
	}
}
