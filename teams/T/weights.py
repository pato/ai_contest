"""
This is the file for defining the weights for our agents. It can also be run as
a program that prints the weights in the appropriate for. See the main function
for more information on this.
"""

#offensive = { 'score': 1.0 }
#offensive = {'foodDownPath': 10.0, 'agentFoodDistance':-5.015006944353908,'disperse':0.5162611055588896,'dontStop':-5145.807103151626,'feasts':-55.047115581965,'ghostDistance':44.353568516626716,'ghostFoodDistance':2.078121539302075,'pacmanDistance':-3.637956876253101,'score':494.8849755629843}
#offensive = {'agentFoodDistance':-6.13169281403951,'disperse':0.1240816945605375,'dontStop':-6174.556841352691,'feasts':-111.18597121422329,'ghostDistance':30.351904504468266,'ghostFoodDistance':1.9795279153381418,'pacmanDistance':-3.645269951232489,'score':675.9370914804919}
#offensive = {'agentFoodDistance':-8.756799781566395,'disperse':0.9092189572995799,'dontStop':-4290.845244111005,'feasts':-125.37448448921515,'ghostDistance':50.23547135970318,'ghostFoodDistance':2.2988748771699736,'pacmanDistance':-3.7381303735807796,'score':783.0366308982319}
#offensive = {'agentFoodDistance':-8.904444886696977,'disperse':1.0414696906450795,'dontStop':-12127.277953518435,'feasts':-1034.1865040893524,'ghostDistance':50.97918744737279,'ghostFoodDistance':1.651378442379878,'pacmanDistance':-29.26105612777171,'score':279.96989732367535}
#offensive = {'agentFoodDistance':-8.651098674855401,'disperse':3.8585068188055973,'dontStop':-10408.254388542864,'feasts':-779.536674122668,'foodDownPath':20.046386707133124,'ghostDistance':53.837701018501875,'ghostFoodDistance':2.5451881318320226,'pacmanDistance':-7.876099711872573,'score':217.31636026497412}
#offensive = {'agentFoodDistance':-8.265134949550575,'disperse':1.6108112643685226,'dontStop':-10000,'feasts':-800,'foodDownPath':15.807036187403249,'ghostDistance':53.8,'ghostFoodDistance':2.5,'pacmanDistance':-7.8,'score':217}
#offensive = {'agentFoodDistance':-8.570681327739509,'disperse':1.4267637933890946,'dontStop':-11053.486700364976,'feasts':-727.964435945695,'foodDownPath':20.071149820762713,'ghostDistance':26.33562578368926,'ghostFoodDistance':2.1033181873413653,'pacmanDistance':-4.400035659018168,'score':867.8759251405045}
#offensive={'agentFoodDistance':-6.87394095697943,'capsuleDistance':-2.467449479493143,'disperse':2.9261564269030638,'dontStop':-4749.098161597775,'feasts':-929.5634579900826,'foodDownPath':31.460901533918186,'ghostDistance':1.3133117111353498,'ghostFoodDistance':1.7694132899744897,'pacmanDistance':-8.803706220875435,'scaredGhostDistance':-3.163579509953692,'score':272.2292467917253}
#offensive={'agentFoodDistance':-6.87394095697943,'capsuleDistance':-2.467449479493143,'disperse':2.9261564269030638,'dontStop':-4749.098161597775,'feasts':-929.5634579900826,'foodDownPath':31.460901533918186,'ghostFoodDistance':3.0,'scaredGhostDistance':-3.163579509953692,'score':272.2292467917253}

# Offensive weights with depth 2
#offensive={'agentFoodDistance':-5.576814605286688,'capsuleDistance':-1.9564308978335214,'disperse':1.4294603446174103,'dontStop':-7836.8400114301585,'feasts':-1104.2610226938614,'foodDownPath':28.398833579293733,'ghostFoodDistance':3.572868589804594,'pacmanDistance':-7.439702045561852,'scaredGhostDistance':-3.8033646361869136,'futureScore':245.63663411308028,'score':100}

#offensive={'agentFoodDistance':-6.032787247064622,'capsuleDistance':-1.4289075858758298,'disperse':2.0644791877194746,'dontStop':-5880.612091187818,'feasts':-1192.269768413758,'foodDownPath':17.033664351999324,'ghostFoodDistance':5.995670599915416,'pacmanDistance':-10.215117832813965,'scaredGhostDistance':-3.7365262839402336,'score':279.78978646778586}

offensive = {'score': 400.0, 'foodDistance': -25.0, 'agentFoodDistance': -5.0, 'ghostDistance': -100.0, 'capsuleDistance': -35.0}

#defensive = { 'score': 1.0 }
defensive = {'pacmanDistance': -50.0, 'onDefense': 100.0, 'disperse': 0.0, 'dontReverse': -8.0, 'dontStop': -100, 'feasts': 0.0}

# If the program is run as main, it will print the weights to the screen in a
# way that is usable by the go program. This is convinient for seeding the
# evolver.
if __name__ == '__main__':
    # Print offensive
    print 'Offensive'
    for name, value in offensive.items():
        print name, value
    
    print
    
    # Print defensive
    print 'Defensive'
    for name, value in defensive.items():
        print name, value
