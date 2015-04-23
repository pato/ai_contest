package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"unicode"
)

type Trial struct {
	trial  int
	winner string
	score  int
}

func main() {
	const NUM_TRIALS = 8
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

	results := make(chan Trial)

	for i := 0; i < NUM_TRIALS; i++ {
		go trial(i, trials[i], defaultDWeights, results)
	}
	for i := 0; i < NUM_TRIALS; i++ {
		fmt.Println(<-results)
	}

	//	for generation := 0; ; generation++ {
	//		log.Printf("Starting %dth generation", generation)
	//		/* Iteration */
	//	}
}

func trial(index int, oweights map[string]float64, dweights map[string]float64, c chan Trial) {

	weightbytes, _ := json.Marshal(oweights)
	weightstring := string(weightbytes)
	weightstring = strings.Replace(weightstring, "\"", "'", -1)

	// Run the simulator
	cmd := exec.Command("python2", "capture.py", "-r", "Dankest", "-z", "0.5", "-i", "400", "-Q", "-k", "2", "-w", weightstring)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}

	err = cmd.Start()
	if err != nil {
		log.Fatal("START FAILED")
		log.Fatal(err)
	}
	log.Printf("Waiting for game to finish...")
	b := make([]byte, 2000)
	n, err := io.ReadFull(stdout, b)
	s := string(b[:n])
	err = cmd.Wait()
	if err != nil {
		log.Fatal("WAIT FAILED")
		log.Fatal(err)
	}

	// Get the results
	lines := strings.Split(s, "\n")
	result := lines[len(lines)-2]
	if result == "Tie game!" {
		/* We have a tie */
		c <- Trial{index, "tie", 0}
	} else {
		/* We have a winner */
		f := func(c rune) bool {
			return unicode.IsSpace(c)
		}
		words := strings.FieldsFunc(result, f)
		team := words[0]
		score, _ := strconv.ParseInt(words[1], 10, 32)
		c <- Trial{index, team, int(score)}
	}
}

/* Time is up.\nTie game! */
/* Time is up.\nThe Blue/Red team wins by X points. */
