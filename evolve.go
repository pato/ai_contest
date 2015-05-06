package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math/rand"
	"os"
	"os/exec"
	"sort"
	"strconv"
	"strings"
	"unicode"
)

const NUM_TRIALS = 8
const NUM_TRIALSPERSTRAND = 10
const NUM_GENERATIONS = 25
const NUM_STEPS = 2000
const TRAIN_OFFENSE = true

type Trial struct {
	trial  int
	winner string
	score  float64
}

type ByScore []Trial

func (a ByScore) Len() int           { return len(a) }
func (a ByScore) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByScore) Less(i, j int) bool { return a[i].score > a[j].score }

func main() {
	var trials [NUM_TRIALS]map[string]float64

	// file, err := os.Open("./teams/T/default")
	// if err != nil {
	// 	log.Fatal(err)
	// }
	// defer file.Close()

	file := os.Stdin
	f := func(c rune) bool {
		return unicode.IsSpace(c)
	}

	var defaultOWeights = make(map[string]float64)
	var defaultDWeights = make(map[string]float64)
	var defaultWeights map[string]float64

	/* Read the default weights */
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

	/* Copy over the map to each trial */
	for i := 0; i < NUM_TRIALS; i++ {
		trials[i] = make(map[string]float64)
		for k, v := range defaultOWeights {
			/* copy over the default map */
			trials[i][k] = v
		}
	}

	/* Run the generations */
	for generation := 0; generation < NUM_GENERATIONS; generation++ {
		log.Printf("Starting %dth generation", generation)
		results := make(chan Trial)

		for i := 0; i < NUM_TRIALS; i++ {
			/* Perform some random permutations */
			for k, v := range trials[i] {
				permute := rand.Float64() > 0.5
				if permute {
					trials[i][k] = v + (rand.NormFloat64() * v / 4)
				}
			}

			/* Run the trial */
			if TRAIN_OFFENSE {
				go trial(i, trials[i], defaultDWeights, results)
			} else {
				go trial(i, defaultOWeights, trials[i], results)
			}
		}

		/* Get the Trial results */
		trialResults := make([]Trial, 8)
		for i := 0; i < NUM_TRIALS; i++ {
			trialResults[i] = <-results
		}

		sort.Sort(ByScore(trialResults))
		fmt.Println(trialResults)

		/* Marry the top 4 results to generate new ones (and the first and second with the fifth to get eight trials) */
		marryTrials(trials, 0, 1, 2)
		marryTrials(trials, 1, 1, 3)
		marryTrials(trials, 2, 1, 4)
		marryTrials(trials, 3, 2, 3)
		marryTrials(trials, 4, 2, 4)
		marryTrials(trials, 5, 3, 4)
		marryTrials(trials, 6, 1, 5)
		marryTrials(trials, 7, 2, 5)

	}
}

func marryTrials(trials [NUM_TRIALS]map[string]float64, dest, dad, mom int) {
	if mom == dad {
		panic("Cannot inbreed")
	}
	avg := func(a, b float64) float64 {
		return (a + b) / 2
	}
	for k, _ := range trials[dest] {
		trials[dest][k] = avg(trials[dad][k], trials[mom][k])
	}
}

func trial(index int, oweights map[string]float64, dweights map[string]float64, c chan Trial) {

	oweightbytes, _ := json.Marshal(oweights)
	oweightstring := string(oweightbytes)
	oweightstring = strings.Replace(oweightstring, "\"", "'", -1)
	oweightstring = fmt.Sprintf("offensiveWeights=%s", oweightstring)
	if TRAIN_OFFENSE {
		fmt.Printf("%d - %s\n", index, oweightstring)
	}
	oweightstring = strings.Replace(oweightstring, ",", "|", -1)

	dweightbytes, _ := json.Marshal(dweights)
	dweightstring := string(dweightbytes)
	dweightstring = strings.Replace(dweightstring, "\"", "'", -1)
	dweightstring = fmt.Sprintf("defensiveWeights=%s", dweightstring)
	if !TRAIN_OFFENSE {
		fmt.Printf("%d - %s\n", index, dweightstring)
	}
	dweightstring = strings.Replace(dweightstring, ",", "|", -1)

	weightstring := "" + oweightstring + "," + dweightstring + "," + "first={'depth':0}" + ""

	stepstring := strconv.Itoa(NUM_STEPS)

	mapstr := "contest01Capture"

	scoreSum := 0.0

	for i := 0; i < NUM_TRIALSPERSTRAND; i++ {
		// Run the simulator
		cmd := exec.Command("python2", "capture.py", "-r", "T", "-z", "0.4", "-i", stepstring, "-k", "4", "-l", mapstr, "--redOpts", weightstring)

		stdout, err := cmd.StdoutPipe()
		cmd.Stderr = os.Stderr
		if err != nil {
			log.Fatal(err)
		}
		//stderr, err := cmd.StderrPipe()
		if err != nil {
			log.Fatal(err)
		}

		err = cmd.Start()
		if err != nil {
			log.Fatal("START FAILED")
			log.Fatal(err)
		}
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
			scoreSum += 0
		} else {
			/* We have a winner */
			f := func(c rune) bool {
				return unicode.IsSpace(c)
			}
			words := strings.FieldsFunc(result, f)
			score, _ := strconv.ParseInt(words[1], 10, 32)
			scoreSum += float64(score)
		}
	}
	//score := scoreSum / NUM_TRIALSPERSTRAND
	c <- Trial{index, "", scoreSum}
}
