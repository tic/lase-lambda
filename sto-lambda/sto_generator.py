from __future__ import print_function

###########################################
### Stuff to make stdout work for me... ###
###########################################

# Collects printed strings to be reported later
strings = []
append = lambda s, end="\n" : strings.append(s + end)
report = lambda : "".join(strings)
reset = lambda : globals().__setitem__('strings', [])

# Back up the actual print method using a *helpful* name
stdout = print

# Replace the print function with our string collecting method
print = append


###################################
### Actual STO generation stuff ###
###################################

global numPoints
numPoints = 5

# All inputs should be arrays of strings
# Used to generate and print an STO

# sets values equal to what user entered
def setValues(name, temp, idle, start, step, flux, exp):
    print("eval min_" + str(temp) + "_temp=" + str(idle))
    print("eval max_" + str(temp) + "_temp=" + str(float(start) + (10 * float(step))))
    print("eval start_" + str(temp) + "_temp=" + str(start))
    print("eval step_" + str(temp) + "_temp=" + str(step))
    print("eval curr_" + str(temp) + "_temp=start_" + str(temp) + "_temp\n")
    print("eval " + str(temp) + "_targetflux=" + str(flux) + "*10^-" + str(exp) + "\n\n")


# outlines structure of wafer being grown
def printStructure(name):
    print("structure (set_" + str(name) + "_temp)")
    print("\teval low=step(min_" + str(name) + "_temp-curr_" + str(name) + "_temp)")
    print("\teval high=step(curr_" + str(name) + "_temp-max_" + str(name) + "_temp)")
    print("\teval curr_" + str(name) + "_temp=min_" + str(name) + "_temp*low+(1-low)*curr_" + str(name) + "_temp")
    print("\teval curr_" + str(name) + "_temp=max_" + str(name) + "_temp*high+(1-high)*curr_" + str(name) + "_temp")
    print("\tt " + str(name) + "=curr_" + str(name) + "_temp")
    print("es\n")


# Finds the average of the fluxes
def takeFlux(name, shutter, num):
    print("comment (" + str(shutter) + " Flux #" + str(num) + ")\n")
    print("eval bg1=0")
    print("eval " + str(name) + "flux=0")
    print("eval avg" + str(name) + "=0")
    print("eval bg2=0")
    print("eval avgbg2=0")
    print("eval bg1=bf\n")

    print("wait 30\n")
    print("repeat 20")
    print("\teval bg2=bf")
    print("\teval avgbg2=avgbg2 + bg2")
    print("\twait 1")
    print("er\n")
    print("open " + str(shutter) + "\n")
    print("wait 60\n")
    print("repeat 30")
    print("\teval " + str(name) + "flux=bf")
    print("\teval avg" + str(name) + "=avg" + str(name) + " + " + str(name) + "flux")
    print("\twait 1")
    print("er\n")
    print("close " + str(shutter) + "\n")

    print("eval avg" + str(name) + "=avg" + str(name) + "/30")
    print("eval avgbg2=avgbg2/20")
    print("eval " + str(name) + "flux=avg" + str(name) + "-avgbg2")
    print("writefile (" + str(name) + "_Flux_Log; \"" + str(name) + "Temp Flux bg1 avgbg2\", curr_" + str(name)
          + "_temp, " + str(name) + "flux, bg1, avgbg2)")

    if num == 'check':
        print("eval " + str(name) + "Error=(" + str(name) + "flux-" + str(name) + "_targetflux)*100/"
              + str(name) + "_targetflux")
        print("writefile (Fluxes; \"" + str(name) + " Temp Flux Target %Difference\", curr" + str(name) + "Temp, "
              + str(name) + ", " + str(name) + "_targetflux, " + str(name) + "Error)\n")

    else:
        print("eval " + str(name) + "T" + str(num) + "=curr_" + str(name) + "_temp")
        print("eval " + str(name) + "BF" + str(num) + "=" + str(name) + "flux")
        if num != 5:
            print("eval curr_" + str(name) + "_temp=curr_" + str(name) + "_temp + step_" + str(name) + "_temp")
            print("set_" + str(name) + "_temp")


# Calculate target temperatures
def calcTemp(name, shutter):
    print("fitexp (", end="")
    first = 1
    for i in range(1, numPoints + 1):
        if first:
            print(str(name) + "T" + str(i), end="")
            first = 0
        else:
            print(", " + str(name) + "T" + str(i), end="")
    first = 1
    for i in range(1, numPoints + 1):
        if first:
            print("; " + str(name) + "BF" + str(i), end="")
            first = 0
        else:
            print(", " + str(name) + "BF" + str(i), end="")
    print("; " + str(name) + "Amp, " + str(name) + "Ea)")
    print("eval " + str(name) + "TargetT=-" + str(name) + "Ea/(8.617385E-5*ln(" + str(name) + "_targetflux/"
          + str(name) + "Amp))-273.15")
    print("eval " + str(name) + "TargetT=(int(" + str(name) + "TargetT*10)/10)")
    print("writefile (TargetTemps; \"" + str(name) + " \", " + str(name) + "TargetT)")
    print("eval curr_" + str(name) + "_temp=" + str(name) + "TargetT")
    print("set_" + str(name) + "_temp\n")


# Generates the recipe using the user inputs
def generateSTO(Group3s, Fluxes, StartTemps, TempSteps, Exp, idletemps, temperatures):
    # calls setValues for each element
    i = 0
    for group3 in Group3s:
        setValues(group3, temperatures[i], idletemps[i], StartTemps[i], TempSteps[i], Fluxes[i], Exp[i])
        printStructure(temperatures[i])
        i += 1

    # set temperatures and wait
    i = 0
    for group3 in Group3s:
        print("t " + str(temperatures[i]) + " = start_" + str(temperatures[i]) + "_temp")
        i += 1

    print("wait 7200\n")

    # getter
    print("waitop (Waiting for user to check everything)\n")
    print("comment (gettering)\n")
    print("repeat 10")

    i = 0
    for group3 in Group3s:
        print("\topen " + str(group3))
        print("\twait 20")
        print("\tclose " + str(group3))
        print("\twait 20")
        i += 1

    print("er\n")
    print("wait 180\n\n")

    # take fluxes(coded for 5 flux STO)
    for j in range(1, 6):
        i = 0
        for group3 in Group3s:
            takeFlux(temperatures[i], group3, j)
            i += 1

        if j != 5:
            wait = 1200 - (i * 80)
            print("\nwait " + str(wait) + "\n")

    # set temperatures
    i = 0
    for group3 in Group3s:
        calcTemp(temperatures[i], group3)
        i += 1

    wait = 1200 - (i * 80)
    print("\nwait " + str(wait) + "\n")

    # check fluxes
    i = 0
    for group3 in Group3s:
        takeFlux(temperatures[i], group3, 'check')
        i += 1

###############################################################

def Generate(Group3s, Fluxes, StartTemps, TempSteps, Exp, idletemps, temperatures):
	reset()
	generateSTO(Group3s, Fluxes, StartTemps, TempSteps, Exp, idletemps, temperatures)
	return report()
#


# Usage example:
#
# def gen():
# 	Group3s = ["Ga", "In"]
# 	Fluxes = ["2.25", "4.00"]
# 	StartTemps = ["1008.2", "865"]
# 	TempSteps = ["5", "5"]
# 	Exp = ["7", "7"]
# 	idletemps = ["350", "350"]
# 	temperatures = ["GaTip", "InTip"]
# 	generateSTO(Group3s, Fluxes, StartTemps, TempSteps, Exp, idletemps, temperatures)
#
# 	output = report()
# 	reset()
# 	return output
