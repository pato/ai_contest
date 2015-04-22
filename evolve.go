package main

import (
	"bufio"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"unicode"
)

func main() {
	const NUM_TRIALS = 2
	var trials [NUM_TRIALS]map[string]float64

	file, err := os.Open("./teams/Dankest/default")
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	f := func(c rune) bool {
		return unicode.IsSpace(c)
	}

	var defaultOWeights = make(map[string]float64)
	var defaultDWeights = make(map[string]float64)
	var defaultWeights map[string]float64

	// Read the default weights
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		words := strings.FieldsFunc(scanner.Text(), f)
		if len(words) == 1 {
			if words[0] == "Offensive" {
				defaultWeights = defaultOWeights
			} else {
				defaultWeights = defaultDWeights
			}
		} else if len(words) == 2 {
			value, _ := strconv.ParseFloat(words[1], 64)
			defaultWeights[words[0]] = value
		}
	}

	// Copy over the map to each trial
	for i := 0; i < NUM_TRIALS; i++ {
		trials[i] = make(map[string]float64)
		for k, v := range defaultOWeights {
			// copy over the default map
			trials[i][k] = v
		}
	}

	team, score := trial(trials[0], defaultDWeights)
	log.Printf("Trial 1: Team: %s with score %d\n", team, score)

	team, score = trial(trials[0], defaultDWeights)
	log.Printf("Trial 2: Team: %s with score %d\n", team, score)

	//	for generation := 0; ; generation++ {
	//		log.Printf("Starting %dth generation", generation)
	//		/* Iteration */
	//		for i := 0; i < NUM_TRIALS; i++ {
	//			go trial(trials[i], defaultDWeights)
	//		}
	//	}
}

func trial(oweights map[string]float64, dweights map[string]float64) (string, int64) {
	// Write the weights file
	f, err := os.Create("ignorews")
	if err != nil {
		panic(err)
	}
	f.WriteString("Offensive\n")
	for feature, weight := range oweights {
		f.WriteString(fmt.Sprintf("%s %.2f\n", feature, weight))
	}
	f.WriteString("\n")
	f.WriteString("Defensive\n")
	for feature, weight := range dweights {
		f.WriteString(fmt.Sprintf("%s %.2f\n", feature, weight))
	}

	// Run the simulator
	cmd := exec.Command("python2", "capture.py", "-r", "Dankest", "-z", "0.5", "-i", "10", "-Q", "-k", "2")
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}

	err = cmd.Start()
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("Waiting for command to finish...")
	b := make([]byte, 2000)
	n, err := io.ReadFull(stdout, b)
	s := string(b[:n])
	err = cmd.Wait()

	// Get the results
	lines := strings.Split(s, "\n")
	result := lines[len(lines)-2]
	if result == "Tie game!" {
		/* We have a tie */
		return "tie", 0
	} else {
		/* We have a winner */
		f := func(c rune) bool {
			return unicode.IsSpace(c)
		}
		words := strings.FieldsFunc(result, f)
		team := words[0]
		//score, _ := strconv.ParseInt(re.ReplaceAllString(result, ""), 10, 64)
		score, _ := strconv.ParseInt(words[1], 10, 64)
		return team, score
	}
	return "", 0
}

/* Time is up.\nTie game! */
/* Time is up.\nThe Blue/Red team wins by X points. */
