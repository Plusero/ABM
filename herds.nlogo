globals [
  base-speed ; base speed for all agents
  base-speed-herd ; base speed for herdanimals, base-speed * herd-speed-ratio
  max-speed-bot ; maximum speed for robots, base-speed-herd * bot-speed-ratio
  max-turn; max turning  per tick
  d0  ; happy-zone-min
  d1  ; happy-zone-max
  k0  ; steepness
  k1  ; steepness
  x0  ; halfwaypoint
  x1  ; halfwaypoint
  knn ; k nearest neighbor
  entity-width
  dt ; time step size
  w-s-max; maximum turning
  target-x ; x-coordinate of the target
  target-y ; y-coordinate of the target
  farmers-vision ; vision of the farmer to collect herdanimals
  fence-range; to prevent animal from being stuck at the edge of the world
]
breed [ herdanimals herdanimal ]
breed [ robots robot ]
breed [ farmers farmer]

herdanimals-own [
  flockmates ; mates for animal-animal interaction
  robotmates ;; mates for animal-robot interaction
  random-mates ; the random one in long-range model of neighbor
  t-force-x ; total force in x-direction
  t-force-y; total force in y-direction
  t-force ; magnitude of total force
  t-force-direction ; direction of total force
  turn ; turning angle
  real-herdanimal-heading ; heading in normal geometry
  speed ; speed of the animal
  dLCM ; distance to the local centre of mass
  dTarget ; distance to the target
]

links-own [
  d-x ; distance-x between two agents
  d-y ; distance-y between two agents
  vector-factor ;; happiness of the animal based on closeness of others and repulsiveness of robot
  force-x; force of this link in x-direction
  force-y; force of this link in y-direction
  real-link-heading
]

robots-own [
  botspeed ; speed of the robot
  real-robot-heading ; heading in normal geometry
  visibles  ; list of all herdanimals that are in unobstructed vision
  furthest-visible ; furthest visible herdanimal
  LCMy;x-coordinate of the local centre of mass
  LCMx ;y-coordinate of the local centre of mass
  distance-traveled;  distance traveled by the robot
]

;; Use a seed created by the NEW-SEED reporter
to use-new-seed
  let my-seed new-seed            ;; generate a new seed
  output-print word "Generated seed: " my-seed  ;; print it out
  random-seed my-seed             ;; use the new seed
  reset-ticks
end

;; Use a seed entered by the user
to use-seed-from-user
  loop [
    let my-seed user-input "Enter a random seed (an integer):"
    carefully [ set my-seed read-from-string my-seed ] [ ]
    ifelse is-number? my-seed and round my-seed = my-seed [
      random-seed my-seed ;; use the new seed
      output-print word "User-entered seed: " my-seed  ;; print it out
      reset-ticks
      stop
    ] [
      user-message "Please enter an integer."
    ]
  ]
end

to setup
  clear-all
  ; set up random seed,  default seed being 73
  if first seed-option = "0" [
    use-new-seed
  ]
  if first seed-option = "1" [
    use-seed-from-user
  ]
  if first seed-option = "2" [
    random-seed 73
  ]
  ; set speed and turning parameters
  set base-speed 0.1
  set base-speed-herd base-speed * herd-speed-ratio
  set max-speed-bot base-speed-herd * bot-speed-ratio
  set dt 1
  set w-s-max 360 ; don't set this value too small, otherwise the herdanimal will have a tendency to go right after flocking together
  ; set up the world
  set fence-range 2
  set-default-shape herdanimals "sheep 2"
  set-default-shape robots   "wolf"
  set-default-shape farmers "person farmer"
  set entity-width 1
  set target-x (- max-pxcor / 2 )
  set target-y (- max-pycor / 2)
  set d0 happyzone-min
  set d1 (happyzone-min + happyzone-max)
  set x0 ( d0 / 2 )
  set x1 ( d1 * 2 )
  set k0 ( 5 / x0 )
  set k1 ( 10 / x1 )
  set knn 5
  create-robots 1 [
    set size 4
    set heading 0
    set color blue
    setxy (- max-pxcor / 2) (max-pycor / 2) ]
  create-herdanimals population
  [ set size 2
    if first model-neighbor != "D"
      [ set color yellow - 2 + random 7 ]  ;; random shades look nice
    setxy random max-pxcor random max-pycor
    rt random-float 360
    set flockmates no-turtles ]
  create-farmers 1
  [
  setxy target-x target-y
  set size 4
  ]
  reset-ticks
end

to go
  clear-links
  ask herdanimals [set color yellow]
  ask robots [list-visibles]
  ask herdanimals [linking]               ; links all the herdanimals with their flockmates
  ask herdanimals [set dTarget (distancexy target-x target-y)] ; get distrance to target from herdanimals
  update-real-heading                     ; converts the inherent headings of all agents to usefull headings,, old headings: NESW 0,90,180,270 -> new headings: NESW
  ask links [link-attribute-calculations] ; calulates the link attributes dx, dy, and happiness
  ask herdanimals [movement]              ; results in movement for the herdanimals
  if auto-shepherd
  [
   ask robots [botmove] ; this procedure results in movement for the robots
   ask farmers [die-on-target] ; results in the death of herdanimals in the farmer's vision
  ]
  tick
end

to list-visibles
  ; get visible herdanimals in the obstructed vision of the robots
  set visibles no-turtles
  ifelse global-vision [
    set visibles (turtle-set visibles herdanimals)
  ][
    foreach [self] of herdanimals [ animal ->
      let ll2 ((distance animal) ^ 2)
      let a2 ((entity-width) ^ 2)
      let arccos (( ll2 - a2 ) / ll2 )
     ifelse arccos < -1 or arccos > 1  [
        set visibles (turtle-set visibles animal)
      ][
        set heading towards animal
        if not any? (herdanimals who-are-not animal) in-cone (distance animal) (acos(arccos)) [
          set visibles (turtle-set visibles animal)
        ]
      ]
    ]
  ]
  if any? visibles [
    set LCMx mean [xcor] of visibles
    set LCMy mean [ycor] of visibles
  ]
  let cmx LCMx
  let cmy LCMy
  ask visibles [set color blue]
  ask visibles [set dLCM (distancexy cmx cmy)]
  set furthest-visible (max-one-of visibles [dLCM])
end

to linking
  ; get robotmates
  set robotmates other robots in-radius robot-repulsion
  create-links-to robotmates
  ; if not any robotmates, then get flockmates. Therefore, robotmates override the interaction with flockmates
  if not any? robotmates[
  ; get flockmates
  if first model-neighbor = "1" [      ; checks which procedure is used for flocking in this case the "1" means considering all other herdanimals in radius vision
    find-flockmates-metric
  ]
  if first model-neighbor = "2" [      ; checks which procedure is used for flocking in this case the "2" means considering only the k nearest neighbours in radius vision
    find-flockmates-knn
  ]
  if first model-neighbor = "3" [      ; checks which procedure is used for flocking in this case the "3" means considering only the k nearest neighbours in radius vision plus one random herdanimal
    find-flockmates-lr
  ]
  create-links-to flockmates     ; this procedure links the herdanimals with their flockmates to make calculations easier
  ]
end

to update-real-heading
  ask links [update-real-heading-l]
  ask robots [update-real-heading-r]
  ask herdanimals [update-real-heading-h]
end

to update-real-heading-l
  if link-length != 0[
    ;convert heading in Netlogo's weird geometry to normal geometry, same for real-heading functions
  set real-link-heading ( - link-heading + 90)
  set real-link-heading (real-link-heading + 180) mod 360 - 180
  ]
end

to update-real-heading-r
  set real-robot-heading ( - heading + 90)
  set real-robot-heading (real-robot-heading + 180) mod 360 - 180
end

to update-real-heading-h
  set real-herdanimal-heading ( - heading + 90)
  set real-herdanimal-heading (real-herdanimal-heading + 180) mod 360 - 180
end

to link-attribute-calculations
  calc-dxdy
  factor-calc
  calc-force
end

to movement
  update-heading
  ifelse any? flockmates[
    fd speed
  ][fd base-speed-herd]
  if xcor > (max-pxcor - fence-range)
  [
    set xcor  (max-pxcor - fence-range)
  ]
  if xcor < ( min-pxcor + fence-range )
  [
    set xcor (  min-pxcor + fence-range)
  ]
  if ycor > (max-pycor - fence-range )
  [
    set ycor ( max-pycor - fence-range)
  ]
  if ycor < (min-pycor + fence-range )
  [
    set ycor ( min-pycor + fence-range)
  ]
end

to find-flockmates-metric   ;; herdanimal procedure
  set flockmates other herdanimals in-radius vision
end

to find-flockmates-knn  ;; herdanimal procedure
  set flockmates other herdanimals in-radius vision
  let num-flockmates count flockmates
  let nn 1
  ifelse num-flockmates >= 0 and num-flockmates < 5 [
  set nn num-flockmates
  ]
  [
  set nn knn
  ]
  set flockmates min-n-of nn flockmates [distance myself]
end

to find-flockmates-lr  ;; herdanimal procedure longrange
  find-flockmates-knn
  let lr-one one-of other herdanimals who-are-not flockmates
  set flockmates (turtle-set flockmates lr-one)
end


to calc-dxdy
  set d-x link-length * cos real-link-heading
  set d-y link-length * sin real-link-heading
end

to factor-calc
  ; use this factor to smooth the transition between the 3 zones, repulsion, alignment, and attraction
  ifelse link-length < d0 [
    set vector-factor (( 1 / ( 1 + exp ( -  k1 * ( (link-length) - x1 )))) - 1 )
  ][
    set vector-factor ( 1 / ( 1 + exp ( -  k0 * ( (link-length)- x0 ))))
  ]
end

to calc-force
  ; this procedure calulates the heading (direction) as well as the stepsize of the herdanimal
  ifelse ([breed] of end1 = herdanimals) and ([breed] of end2 = herdanimals) [
    ifelse (link-length >= d0)[
    let alignment-force-x ((cos (sum [real-herdanimal-heading] of both-ends) / 2 ) * alignment-weight *(1 - vector-factor))
    let alignment-force-y ((sin (sum [real-herdanimal-heading] of both-ends) / 2 ) * alignment-weight *(1 - vector-factor))
    let attraction-force-x (d-x  * attraction-weight * vector-factor)
    let attraction-force-y (d-y  * attraction-weight * vector-factor)
    set force-x (alignment-force-x + attraction-force-x)
    set force-y (alignment-force-y + attraction-force-y)
    set color green
  ][
     set force-x (d-x) * vector-factor * repulsion-weight
     set force-y (d-y) * vector-factor * repulsion-weight
     set color red
  ]
  ]
  [
     set force-x (- d-x)  * vector-factor * repulsion-weight
     set force-y (- d-y)  * vector-factor * repulsion-weight
     set color red
  ]
end

to update-heading
  set t-force-x (sum [ force-x ] of my-out-links )
  set t-force-y (sum [ force-y ] of my-out-links )
  set t-force sqrt (t-force-x * t-force-x + t-force-y * t-force-y)
  ifelse t-force-x = 0 and t-force-y = 0[
    set turn 0
  ]
  [
    ;; make sure that the angle in Netlogo geometry is converted to normal geometry
    let arctan-normal (-(atan t-force-x t-force-y) + 90)
    ;;  converted to [-π, π]
    set t-force-direction (arctan-normal + 180) mod 360 - 180
    ;;rotating duration (limited)
    set turn (real-herdanimal-heading - t-force-direction)
    let dt-w min (list (abs(turn) / w-s-max) dt)
    let turn-sign 1
    if turn < 0 [
    set turn-sign -1
    ]
    set turn (turn-sign * w-s-max * dt-w)
    set heading heading + turn
    ; scale speed
    let speed-factor t-force / 100
    if speed-factor > 1[
    set speed-factor 1
    ]
    set speed base-speed-herd * speed-factor
  ]
  set heading (heading - Randomness / 2  + random Randomness) ; to add randomness of movement
  ; this procedure updates the heading (direction) of the herdanimal
end


to botmove
  ; move that botty
  if any? visibles[
  let closest-ha (min-one-of visibles [distance myself])
    ifelse (distance closest-ha) < min-distance-to-herd [
    set botspeed 0.01
  ][
    set botspeed 1
  ]
  ifelse [dLCM] of furthest-visible > furthest-allowed [
    let x-comp ([xcor] of furthest-visible - LCMx)
    let y-comp ([ycor] of furthest-visible - LCMy)
    let c-comp ([dLCM] of furthest-visible)
    let ratio ((c-comp + min-distance-to-herd) / c-comp)
    set x-comp (x-comp * ratio)
    set y-comp (y-comp * ratio)
    set heading towardsxy (LCMx + x-comp) (LCMy + y-comp)
  ][
    let furthest-from-target (max-one-of visibles [distancexy target-x target-y])
    let x-comp ([xcor] of furthest-from-target - target-x)
    let y-comp ([ycor] of furthest-from-target - target-y)
    let dist ([dTarget] of furthest-from-target)
    let ratio ((dist + min-distance-to-herd) / dist)
    set x-comp (x-comp * ratio)
    set y-comp (y-comp * ratio)
    set heading towardsxy (target-x + x-comp) (target-y + y-comp)
  ]
  fd max-speed-bot * botspeed
  set distance-traveled ( distance-traveled + max-speed-bot * botspeed )
  ]
end

to move-up
  ask robots [ set heading 0
  fd 1]
end

to move-right
  ask robots [ set heading 90
    fd 1]

end

to move-down
  ask robots [ set heading 180
  fd 1]
end

to move-left
  ask robots [ set heading 270
  fd 1]
end

to die-on-target
  if  any? herdanimals in-radius farmer-vision[
    ask herdanimals in-radius farmer-vision [die]
  ]
end

  ; Copyright 1998 Uri Wilensky.
  ; See Info tab for full copyright and license.
@#$#@#$#@
GRAPHICS-WINDOW
272
10
847
586
-1
-1
7.0
1
10
1
1
1
0
0
0
1
-40
40
-40
40
1
1
1
ticks
30.0

BUTTON
8
13
85
46
NIL
setup
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
91
13
172
46
go
go
T
1
T
OBSERVER
NIL
NIL
NIL
NIL
0

SLIDER
8
78
231
111
population
population
1
100
50.0
1
1
NIL
HORIZONTAL

SLIDER
8
115
231
148
vision
vision
0
50
25.0
0.5
1
patches
HORIZONTAL

CHOOSER
7
261
181
306
model-neighbor
model-neighbor
"0 None" "1 Metric neighbor" "2 Topological neighbor" "3 Long-range neighbor"
3

SLIDER
8
221
181
254
happyzone-min
happyzone-min
0
100
2.0
0.1
1
NIL
HORIZONTAL

SLIDER
8
182
181
215
happyzone-max
happyzone-max
0
100
13.0
0.1
1
NIL
HORIZONTAL

SLIDER
7
309
179
342
repulsion-weight
repulsion-weight
0
100
100.0
0.01
1
NIL
HORIZONTAL

SLIDER
7
345
179
378
alignment-weight
alignment-weight
0
50
50.0
0.01
1
NIL
HORIZONTAL

SLIDER
7
382
179
415
attraction-weight
attraction-weight
0
1
1.0
0.01
1
NIL
HORIZONTAL

BUTTON
182
12
260
46
go-once
go
NIL
1
T
OBSERVER
NIL
Q
NIL
NIL
1

BUTTON
940
439
1003
472
up
move-up
NIL
1
T
OBSERVER
NIL
W
NIL
NIL
1

BUTTON
939
477
1002
510
down
move-down
NIL
1
T
OBSERVER
NIL
S
NIL
NIL
1

BUTTON
872
476
935
509
left
move-left
NIL
1
T
OBSERVER
NIL
A
NIL
NIL
1

BUTTON
1008
477
1071
510
right
move-right
NIL
1
T
OBSERVER
NIL
D
NIL
NIL
1

SLIDER
9
420
181
453
robot-repulsion
robot-repulsion
0
20
10.0
1
1
NIL
HORIZONTAL

SLIDER
8
458
180
491
Randomness
Randomness
0
10
5.0
0.1
1
NIL
HORIZONTAL

SWITCH
871
397
1007
430
auto-shepherd
auto-shepherd
0
1
-1000

BUTTON
866
66
1005
99
use-new-seed
use-new-seed
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
867
108
1006
141
use-seed-from-user
use-seed-from-user
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

SLIDER
867
150
1010
183
farmer-vision
farmer-vision
0
10
5.0
1
1
NIL
HORIZONTAL

SLIDER
7
502
180
535
herd-speed-ratio
herd-speed-ratio
0
10
1.0
1
1
NIL
HORIZONTAL

SLIDER
9
544
182
577
bot-speed-ratio
bot-speed-ratio
0
10
5.0
0.1
1
NIL
HORIZONTAL

SWITCH
868
226
997
259
global-vision
global-vision
1
1
-1000

CHOOSER
867
12
1005
57
seed-option
seed-option
"0 Random" "1 user-input" "2 fixed"
0

SLIDER
867
272
1039
305
furthest-allowed
furthest-allowed
0
50
25.0
1
1
NIL
HORIZONTAL

SLIDER
868
314
1040
347
min-distance-to-herd
min-distance-to-herd
0
10
5.0
1
1
NIL
HORIZONTAL

TEXTBOX
13
55
163
73
Animal Generation
16
0.0
1

TEXTBOX
9
153
195
187
Interaction Parameters
16
0.0
1

TEXTBOX
868
199
1116
233
Herding Strategy Parameters
16
0.0
1

TEXTBOX
873
366
1023
384
Debuggers
16
0.0
1

@#$#@#$#@
## ACKNOWLEDGMENT

This model is an alternate visualization of the Flocking model from the Biology section of the NetLogo Models Library. It uses visualization techniques as recommended in the paper:

* Kornhauser, D., Wilensky, U., & Rand, W. (2009). Design guidelines for agent based model visualization. Journal of Artificial Societies and Social Simulation (JASSS), 12(2), 1. http://ccl.northwestern.edu/papers/2009/Kornhauser,Wilensky&Rand_DesignGuidelinesABMViz.pdf.

## WHAT IS IT?

This model is

This model is a version of the NetLogo Flocking model that adds visualizations.
The Flocking model is an attempt to mimic the flocking of birds.  (The resulting motion also resembles schools of fish.)  The flocks that appear in this model are not created or led in any way by special leader birds.  Rather, each bird (aka boid) is following exactly the same set of rules, from which flocks emerge.

The birds follow three rules: "alignment", "separation", and "cohesion".  "Alignment" means that a bird tends to turn so that it is moving in the same direction that nearby birds are moving.  "Separation" means that a bird will turn to avoid another bird which gets too close.  "Cohesion" means that a bird will move towards other nearby birds (unless another bird is too close).  When two birds are too close, the "separation" rule overrides the other two, which are deactivated until the minimum separation is achieved.

The three rules affect only the bird's heading.  Each bird always moves forward at the same constant speed.

This version creates 4 different visualizations of the model, depending on which question about the model you are trying to answer.

## HOW TO USE IT

First, determine the number of birds you want in the simulation and set the POPULATION slider to that value.  Press SETUP to create the birds, and press GO to have them start flying around.

The default settings for the sliders will produce reasonably good flocking behavior.  However, you can play with them to get variations:

Three TURN-ANGLE sliders control the maximum angle a bird can turn as a result of each rule.

VISION is the distance that each bird can see 360 degrees around it.

STEP is the distance a bird moves at each tick.

VISUALIZATION
Each visualization is designed to highlight the answers to specific questions.
QUESTION has 5 values. Each value results in a different visualization that helps answer the corresponding question.
Value of 0 = "NONE". This gives the same behavior as the standard flocking model.
Value of 1 = "Are the boids aligned". Boids with the same direction have the same color. Clusters with the same heading can be easily distinguished.
Value of 2 = "Are the boids in separation or cohesion mode?". This colors the boids red when they are separating and green when they are cohering.
Value of 3 = "Do all of the boids end up following the same leader?". Each flock gets a different color.
Value of 4 = "Are the boids aligned? Are the boids in separation or cohesion mode?". Boids with the same direction have the same color. Boids in separation mode have the default shape, Boids in cohesion mode have a "line" shape.

## THINGS TO NOTICE

Central to the model is the observation that flocks form without a leader.

There are no random numbers used in this model, except to position the birds initially.  The fluid, lifelike behavior of the birds is produced entirely by deterministic rules.

Also, notice that each flock is dynamic.  A flock, once together, is not guaranteed to keep all of its members.  Why do you think this is?

After running the model for a while, all of the birds have approximately the same heading.  Why?

Sometimes a bird breaks away from its flock.  How does this happen?  You may need to slow down the model or run it step by step in order to observe this phenomenon.

## THINGS TO TRY

Play with the sliders to see if you can get tighter flocks, looser flocks, fewer flocks, more flocks, more or less splitting and joining of flocks, more or less rearranging of birds within flocks, etc.

You can turn off a rule entirely by setting that rule's angle slider to zero.  Is one rule by itself enough to produce at least some flocking?  What about two rules?  What's missing from the resulting behavior when you leave out each rule?

Will running the model for a long time produce a static flock?  Or will the birds never settle down to an unchanging formation?  Remember, there are no random numbers used in this model.

## EXTENDING THE MODEL

Currently the birds can "see" all around them.  What happens if birds can only see in front of them?  The `in-cone` primitive can be used for this.

Is there some way to get V-shaped flocks, like migrating geese?

What happens if you put walls around the edges of the world that the birds can't fly into?

Can you get the birds to fly around obstacles in the middle of the world?

What would happen if you gave the birds different velocities?  For example, you could make birds that are not near other birds fly faster to catch up to the flock.  Or, you could simulate the diminished air resistance that birds experience when flying together by making them fly faster when in a group.

Are there other interesting ways you can make the birds different from each other?  There could be random variation in the population, or you could have distinct "species" of bird.

Can you add a value to the QUESTION chooser and develop a corresponding visualization that helps answer the question?

## NETLOGO FEATURES

Notice the need for the `subtract-headings` primitive and special procedure for averaging groups of headings.  Just subtracting the numbers, or averaging the numbers, doesn't give you the results you'd expect, because of the discontinuity where headings wrap back to 0 once they reach 360.

## RELATED MODELS

* Moths
* Flocking Vee Formation

## CREDITS AND REFERENCES

This model is inspired by the Boids simulation invented by Craig Reynolds.  The algorithm we use here is roughly similar to the original Boids algorithm, but it is not the same.  The exact details of the algorithm tend not to matter very much -- as long as you have alignment, separation, and cohesion, you will usually get flocking behavior resembling that produced by Reynolds' original model.  Information on Boids is available at https://web.archive.org/web/20210818090425/http://www.red3d.com/cwr/boids/.

To refer to this model in academic publications, please use:  Wilensky, U. (1998).  NetLogo Flocking model.  http://ccl.northwestern.edu/netlogo/models/Flocking.  Center for Connected Learning and Computer-Based Modeling, Northwestern University, Evanston, IL.

In other publications, please use:  Copyright 1998 Uri Wilensky.  All rights reserved.  See http://ccl.northwestern.edu/netlogo/models/Flocking for terms of use.

## HOW TO CITE

If you mention this model or the NetLogo software in a publication, we ask that you include the citations below.

For the model itself:

* Wilensky, U. (1998).  NetLogo Flocking - Alternative Visualizations model.  http://ccl.northwestern.edu/netlogo/models/Flocking-AlternativeVisualizations.  Center for Connected Learning and Computer-Based Modeling, Northwestern University, Evanston, IL.

Please cite the NetLogo software as:

* Wilensky, U. (1999). NetLogo. http://ccl.northwestern.edu/netlogo/. Center for Connected Learning and Computer-Based Modeling, Northwestern University, Evanston, IL.

## COPYRIGHT AND LICENSE

Copyright 1998 Uri Wilensky.

![CC BY-NC-SA 3.0](http://ccl.northwestern.edu/images/creativecommons/byncsa.png)

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 License.  To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.

Commercial licenses are also available. To inquire about commercial licenses, please contact Uri Wilensky at uri@northwestern.edu.

This model was created as part of the projects: PARTICIPATORY SIMULATIONS: NETWORK-BASED DESIGN FOR SYSTEMS LEARNING IN CLASSROOMS and/or INTEGRATED SIMULATION AND MODELING ENVIRONMENT. The project gratefully acknowledges the support of the National Science Foundation (REPP & ROLE programs) -- grant numbers REC #9814682 and REC-0126227.

<!-- 1998 -->
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300
Line -7500403 true 150 0 150 75
Rectangle -7500403 true true 150 0 150 60
Rectangle -7500403 true true 135 15 135 75

line half
true
0
Line -7500403 true 150 0 150 150

link
true
0
Line -7500403 true 150 0 150 300

link direction
true
0
Line -7500403 true 150 150 30 225
Line -7500403 true 150 150 270 225

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

person farmer
false
0
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Polygon -1 true false 60 195 90 210 114 154 120 195 180 195 187 157 210 210 240 195 195 90 165 90 150 105 150 150 135 90 105 90
Circle -7500403 true true 110 5 80
Rectangle -7500403 true true 127 79 172 94
Polygon -13345367 true false 120 90 120 180 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 180 90 172 89 165 135 135 135 127 90
Polygon -6459832 true false 116 4 113 21 71 33 71 40 109 48 117 34 144 27 180 26 188 36 224 23 222 14 178 16 167 0
Line -16777216 false 225 90 270 90
Line -16777216 false 225 15 225 90
Line -16777216 false 270 15 270 90
Line -16777216 false 247 15 247 90
Rectangle -6459832 true false 240 90 255 300

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep 2
false
0
Polygon -7500403 true true 209 183 194 198 179 198 164 183 164 174 149 183 89 183 74 168 59 198 44 198 29 185 43 151 28 121 44 91 59 80 89 80 164 95 194 80 254 65 269 80 284 125 269 140 239 125 224 153 209 168
Rectangle -7500403 true true 180 195 195 225
Rectangle -7500403 true true 45 195 60 225
Rectangle -16777216 true false 180 225 195 240
Rectangle -16777216 true false 45 225 60 240
Polygon -7500403 true true 245 60 250 72 240 78 225 63 230 51
Polygon -7500403 true true 25 72 40 80 42 98 22 91
Line -16777216 false 270 137 251 122
Line -16777216 false 266 90 254 90

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -7500403 true true 75 225 97 249 112 252 122 252 114 242 102 241 89 224 94 181 64 113 46 119 31 150 32 164 61 204 57 242 85 266 91 271 101 271 96 257 89 257 70 242
Polygon -7500403 true true 216 73 219 56 229 42 237 66 226 71
Polygon -7500403 true true 181 106 213 69 226 62 257 70 260 89 285 110 272 124 234 116 218 134 209 150 204 163 192 178 169 185 154 189 129 189 89 180 69 166 63 113 124 110 160 111 170 104
Polygon -6459832 true true 252 143 242 141
Polygon -6459832 true true 254 136 232 137
Line -16777216 false 75 224 89 179
Line -16777216 false 80 159 89 179
Polygon -6459832 true true 262 138 234 149
Polygon -7500403 true true 50 121 36 119 24 123 14 128 6 143 8 165 8 181 7 197 4 233 23 201 28 184 30 169 28 153 48 145
Polygon -7500403 true true 171 181 178 263 187 277 197 273 202 267 187 260 186 236 194 167
Polygon -7500403 true true 187 163 195 240 214 260 222 256 222 248 212 245 205 230 205 155
Polygon -7500403 true true 223 75 226 58 245 44 244 68 233 73
Line -16777216 false 89 181 112 185
Line -16777216 false 31 150 47 118
Polygon -16777216 true false 235 90 250 91 255 99 248 98 244 92
Line -16777216 false 236 112 246 119
Polygon -16777216 true false 278 119 282 116 274 113
Line -16777216 false 189 201 203 161
Line -16777216 false 90 262 94 272
Line -16777216 false 110 246 119 252
Line -16777216 false 190 266 194 274
Line -16777216 false 218 251 219 257
Polygon -16777216 true false 230 67 228 54 222 62 224 72
Line -16777216 false 246 67 234 64
Line -16777216 false 229 45 235 68
Line -16777216 false 30 150 30 165

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270
@#$#@#$#@
NetLogo 6.4.0
@#$#@#$#@
set population 200
setup
repeat 200 [ go ]
@#$#@#$#@
@#$#@#$#@
<experiments>
  <experiment name="global vs local" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <enumeratedValueSet variable="global-vision">
      <value value="true"/>
      <value value="false"/>
    </enumeratedValueSet>
  </experiment>
  <experiment name="bot-speed" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="bot-speed-ratio" first="1" step="1" last="10"/>
  </experiment>
  <experiment name="furthest-allowed" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="furthest-allowed" first="15" step="5" last="40"/>
  </experiment>
  <experiment name="min-distance-to-herd" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="min-distance-to-herd" first="3" step="1" last="9"/>
  </experiment>
  <experiment name="population" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="population" first="10" step="10" last="100"/>
  </experiment>
  <experiment name="bot-speed-finer" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="bot-speed-ratio" first="1" step="0.1" last="2"/>
  </experiment>
  <experiment name="bot-speed-global-local" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="bot-speed-ratio" first="1" step="1" last="10"/>
    <enumeratedValueSet variable="global-vision">
      <value value="true"/>
      <value value="false"/>
    </enumeratedValueSet>
  </experiment>
  <experiment name="min-distance-to-herd-global-local" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="min-distance-to-herd" first="3" step="1" last="9"/>
    <enumeratedValueSet variable="global-vision">
      <value value="true"/>
      <value value="false"/>
    </enumeratedValueSet>
  </experiment>
  <experiment name="population-global-local" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="population" first="10" step="10" last="100"/>
    <enumeratedValueSet variable="global-vision">
      <value value="true"/>
      <value value="false"/>
    </enumeratedValueSet>
  </experiment>
  <experiment name="furthest-allowed-global-local" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="furthest-allowed" first="15" step="5" last="40"/>
    <enumeratedValueSet variable="global-vision">
      <value value="true"/>
      <value value="false"/>
    </enumeratedValueSet>
  </experiment>
  <experiment name="bot-speed-finer-global-local" repetitions="30" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <exitCondition>not any? herdanimals or ticks = 10000</exitCondition>
    <metric>ticks</metric>
    <metric>[distance-traveled] of robots</metric>
    <runMetricsCondition>not any? herdanimals or ticks = 10000</runMetricsCondition>
    <steppedValueSet variable="bot-speed-ratio" first="1" step="0.1" last="2"/>
    <enumeratedValueSet variable="global-vision">
      <value value="true"/>
      <value value="false"/>
    </enumeratedValueSet>
  </experiment>
</experiments>
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
