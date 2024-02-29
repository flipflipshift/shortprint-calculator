import streamlit as st
import scipy.stats as stats
from scipy.stats import chi2, binomtest, beta
from scipy.special import gamma, betainc
import pandas as pd




st.title('Short print confidence calculator')

st.write('''
	When initial data comes about about print ratios in a set and we see 
	the most sought-after cards appear much less frequently than they should, we frequently wonder if this is a coincidence 
	or if the card is genuinely under-printed. How can we better quantize our uncertainty? We provide three approaches here.
	''')

st.title('Option 1')

st.write('''For the first option, we look at one rarity at a time. 
	For the rarity of your choice, input all card quantities that you know of. You can input multiple at a time by writing multiple quantities separated by commas.''')


# Initialize session state for storing numbers
if 'numbers' not in st.session_state:
    st.session_state.numbers = []
    st.session_state.sum=0

st.text_input('Enter quantities, separated by a comma',key='to_add_text')
if st.button('Add quantities'):
		try:
			to_add_text=st.session_state['to_add_text']
			to_add = [int(item.strip()) for item in to_add_text.split(',')]
			st.session_state.numbers.extend(to_add)
			st.session_state.sum += sum(to_add)
		except ValueError:
			st.warning('Please enter only integers, separated by commas.')

for i in range(len(st.session_state.numbers)):
	st.write(f"Card {i+1} frequency: {st.session_state.numbers[i]}")
st.write(f"Distinct cards entered: {len(st.session_state.numbers)} , Total number of cards: {st.session_state.sum}")

st.number_input('Clear this many values from the end: ', value=0, min_value=0, key='remove_range', format='%d')
if st.button('Remove last quantities'):
	remove_range=st.session_state['remove_range']
	if remove_range>len(st.session_state.numbers):
		st.warning('Please enter a number smaller than the size of the current list.')
	else:
		st.session_state.numbers=st.session_state.numbers[:-remove_range] if remove_range else st.session_state.numbers #check
		st.session_state.sum=sum(st.session_state.numbers)
		st.experimental_rerun()
if st.button('Clear all'):
	st.session_state.numbers=[]
	st.session_state.sum=0
	st.experimental_rerun()


st.write('''Enter the number of distinct cards in the chosen rarity, and the total number of cards in that rarity that have been pulled so far. 
	If you inputted all the quantities in the rarity, these will be the numbers that appear above. If you do not know the exact number of total cards in that rarity that have been pulled so far, 
	you can provide an estimate (for example if 3000 packs were opened and there is 1 ultra rare every 4 packs, you would estimate that 
there are a total of 3000/4=750 ultra rare cards).
	''')
#Input + button
num_cards=st.number_input('Number of distinct cards in rarity : ', value=len(st.session_state.numbers), format='%d')
total_cards=st.number_input('Total number of cards: ', value=st.session_state.sum, format='%d')

st.write('''For our first piece of analysis, we ask for the probability that our observations would be as abnormal as our observations 
	were if the cards were really evenly distributed. This is known as the p-value, and is displayed in scientific notation. In many scientific disciplines, p-values less than 
	.05 or .01 are taken as justification for accepting the alternative hypothesis (in this case, that the cards are not actually evenly distributed).
	''')

if st.button('Calculate p-value'):
	if total_cards< st.session_state.sum:
		st.warning('Number of distinct cards must be at least number of distinct cards entered.')
	elif num_cards<len(st.session_state.numbers):
		st.warning('Total number of cards must be at least total of entered card quantities.')
	elif not (num_cards==len(st.session_state.numbers)) == (total_cards==st.session_state.sum):
		st.warning('If the total number of cards matches the total number of entered cards, the number of distinct cards must match as well (and vice versa).')
	else:
		avg=total_cards/num_cards
		card_diff=total_cards-st.session_state.sum
		cat_diff=num_cards-len(st.session_state.numbers)
		pearson_statistic=sum(((i-avg)**2) for i in st.session_state.numbers)/avg
		if cat_diff!=0:
			pearson_statistic += cat_diff*((cat_diff/card_diff-avg)**2)/avg
		#running_sum+=cat_diff*((cat_diff/card_diff-avg)**2)/avg
		st.session_state.p_value=chi2.sf(pearson_statistic, num_cards-1)
if 'p_value' in st.session_state:
	st.write(st.session_state.p_value)


st.write('''We define the 'true frequency ratio' of a card to be the its true frequency divided by what the frequency would have been if there 
	were no short prints. So a true frequency ratio of .5 means the card's true frequency is half of what it would have been without short prints.  The 'observed frequency ratio' of a card is its observed frequency divided by what the frquency 
	would have been if there were no short prints. We use frequency ratios isntead of frequencies for the sake of easy readability and interpretability.''')

st.write('''After clicking the below button, you will see a table of the observed frequency ratios of each card, along with two upper confidence bounds for its true frequency ratios. For each 
card, there is a 95\% chance that its true frequency ratio is below the individual upper confidence bound. And there is at least a 
95\% chance that *all* cards' true frequency ratios are below the simulteanous upper confidence bound. That 95\% can be modified from 70\% to 99.99999\% in 
the 'confidence level' box below. ''')

confidence_value = st.number_input("Input confidence level above 70 and below 100:", value=95.0, min_value=70.0, max_value=99.99999, step=0.01,format="%.5f")

if st.button('Compute confidence bounds', key='confidence_compute'):
	alpha=(1-(confidence_value)/100)
	observed_freq=[x/total_cards*num_cards for x in st.session_state.numbers]
	indivs=[num_cards*(stats.beta.interval(1-alpha, x+1,total_cards-x)[1]) for x in st.session_state.numbers]
	simuls=[num_cards*(stats.beta.interval(1-alpha/num_cards, x+1,total_cards-x)[1]) for x in st.session_state.numbers]
	df = pd.DataFrame({'Observed frequency ratio':observed_freq,  'Individual confidence bound': indivs, 'Simultaneous confidence bound': simuls}, index=[f'Card {i+1}' for i in range(len(indivs))])
	st.table(df)




st.write('''To ensure these bounds are being interpreted correctly, we will make the notion of confidence bounds precise, sticking to 95\% to keep things 
	simple. Let's say there are 
	100 different game stores opening cases and inputting their data into this website. Roughly 95 of them will see an upper individual confidence 
	bound for Card 1 that is at or above the true frequency ratio of Card 1 and about 5 of them will incorrectly see an upper individual confidence below the frequency ratio because they (by pure chance) happened to pull 
	very few copies of Card 1. On the other hand, roughly 95 of them will have *all* 95\% simultaneous upper confidence bounds at or above the true 
	frequency ratios. This is a frequentist approach to statistics; if it seems strange, Option 3 
	will take a different approach.''')

#st.write(''' The purpose of the simultaneous upper bounds is to avoid what is called p-hacking. Each individual upper confidence bound has a high chance to be 
#	correct, but there is also a good chance that at least one of them is incorrect. While the simultaneous upper confidence bounds do not have this issue, they play 
#	it unnecessarily safe by taking all cards into account simultaneously instead of just the interesting ones. This is improved in Option 2.''')

st.title('Option 2')

st.write('''By being a little smarter, we can actually lower our simultaneous upper confidence bounds. The reason we care about simultaneous confidence bounds 
	is that if there are many cards of a given rarity, 
	there is a high chance that at least one of the individual 95\% confidence bounds are wrong but 
	at most a 5\% chance that any of the simultaneous confidence bounds are wrong. But we don't need to take all cards 
	into account; there are usually only a few cards that we will suspect of short-printing.
	''')

st.write('''For this option, you pretend that you have not seen any data yet, and list all the cards that are good candidates to be short-printed. It is important that 
	you perform this step honestly and do not simply choose the cards that happened to have the lowest print ratios so far. Ideally, you would list the candidates before you observe the data at all.
	For each of these cards, list the Card Name, the number of that card that was pulled, the number of cards that share its rarity (including itself), and the odds of that rarity. For instance, 
	if the card is Ultra rare, there are 8 ultra rares in the set, and the odds of an ultra rare in a pack are 1:4, then you would enter '8' and '4'. ''')


col1, col2, col3, col4 = st.columns(4)
if 'entries' not in st.session_state:
	st.session_state.entries=[]

with col1:
    name = st.text_input('Card Name:', value='')
with col2:
    quantity = st.number_input('Observed quantity:', value=0, format="%d")
with col3:
    rarity_number = st.number_input('# Cards in rarity:', value=1, format="%d")
with col4:
    odds = st.number_input('Rarity Odds:', value=1, format="%d")

if st.button('Add to list'):
	if odds<=0 or rarity_number<=0 or quantity<=0:
		st.error("Please enter positive integer values")
	else:
		st.session_state.entries.append([name,quantity, odds, rarity_number, odds*rarity_number])
for i in range(len(st.session_state.entries)):
	entry=st.session_state.entries[i]
	st.write(f"Card {i+1} Name: {entry[0]}, Quantity: {entry[1]}, Cards in rarity: {entry[2]}, Rarity odds: {entry[3]}, Expected frequency: 1/{entry[4]}")

st.number_input('Clear this many values from the end: ', value=0, min_value=0, key='remove_range_2', format='%d')
if st.button('Remove last quantities', key='second remove'):
	remove_range=st.session_state['remove_range_2']
	if remove_range>len(st.session_state.entries):
		st.warning('Please enter a number smaller than the size of the current list.')
	else:
		st.session_state.entries=st.session_state.entries[:-remove_range] if remove_range else st.session_state.entries #check
		st.experimental_rerun()
if st.button('Clear all', key='second clear'):
	st.session_state.entries=[]
	st.experimental_rerun()

st.write('Enter the total number of packs that have been opened and your desired confidence level. Then click "compute" for the individual and simultaneous upper confidence bounds on the frequency ratios.')
total_packs=st.number_input('Enter total number of packs opened', min_value=1, format="%d", value=100)
confidence_value_2 = st.number_input("Input confidence level above 70 and below 100:",key='confidence_2', value=95.0, min_value=70.0, max_value=99.99999, step=0.01,format="%.5f")

if st.button('Compute confidence bounds'):
#On button  clikc:
	dic=st.session_state.entries
	alpha_2=(1-(confidence_value_2)/100)
	observed_freq_2=[x[1]/total_packs*x[4] for x in dic]
	indivs_2=[x[4]*(stats.beta.interval(1-alpha, x[1]+1,total_packs-x[1])[1]) for x in dic]
	simuls_2=[x[4]*(stats.beta.interval(1-alpha/len(dic), x[1]+1,total_packs-x[1])[1]) for x in dic]
	df2 = pd.DataFrame({'Observed frequency ratio':observed_freq_2,  'Individual confidence bound': indivs_2, 'Simultaneous confidence bound': simuls_2}, index=[dic[i][0] for i in range(len(dic))])
	st.table(df2)


st.title('Option 3')

st.write('''If a card's 95\% upper simultaneous confidence bound on it frequency ratio is less than 1, 
	should we be 95\% sure that the card is short printed? If Konami never short-printed a set before, we would probably be less sure than we would 
	if Konami regularly engaged in short printing sets of that type. We want to factor in our prior beliefs about short printing to get 
	an accurate idea of how we should update our beliefs from this data. This is the Bayesian approach, which contrasts with our 
	earlier frequentist approach. To avoid bias, you will need to input the quantities of every card for a given rarity in this section.''')

if 'numbers_2' not in st.session_state:
    st.session_state.numbers_2 = []
    st.session_state.sum_2=0


st.text_input('Enter quantities, separated by a comma',key='to_add_text_2')
if st.button('Add quantities', key='add_quantity_2'):
		try:
			to_add_text=st.session_state['to_add_text_2']
			to_add = [int(item.strip()) for item in to_add_text.split(',')]
			st.session_state.numbers_2.extend(to_add)
			st.session_state.sum_2 += sum(to_add)
		except ValueError:
			st.warning('Please enter only integers, separated by commas.')

for i in range(len(st.session_state.numbers_2)):
	st.write(f"Card {i+1} frequency: {st.session_state.numbers_2[i]}")
st.write(f"Distinct cards entered: {len(st.session_state.numbers_2)} , Total number of cards: {st.session_state.sum_2}")

st.number_input('Clear this many values from the end: ', value=0, min_value=0, key='remove_range_3', format='%d')
if st.button('Remove last quantities', key='remove_button_3'):
	remove_range_3=st.session_state['remove_range_3']
	if remove_range_3>len(st.session_state.numbers_2):
		st.warning('Please enter a number smaller than the size of the current list.')
	else:
		st.session_state.numbers_2=st.session_state.numbers_2[:-remove_range_3] if remove_range_3 else st.session_state.numbers_2 #check
		st.session_state.sum_2=sum(st.session_state.numbers_2)
		st.experimental_rerun()
if st.button('Clear all', key='clear_all_2'):
	st.session_state.numbers_2=[]
	st.session_state.sum_2=0
	st.experimental_rerun()

st.write('''Next, enter a rough estimate of how likely you thought it was that the set would have no short-prints, before any data was released. 
	This is supposed to be a subjective question; it can be based on how many sets like it were recently short-printed or just based on a gut feeling. The more data 
	you have, the less your answer here will actually matter (you can see this for yourelf by playing with different prior probabilities.)''')

prior = st.number_input("Input likelihood of no short-prints:", value=50, min_value=1, max_value=99, step=1)

st.write('''If there are short-prints, then there are infinitely many possibilities for the true frequencies that each card shows up. To keep the math simple, 
	we will treat these all equally likely (in techinical terms, our prior will be a weighted average of a degenerate distribution and a uniform distribution over the hypothesis 
	space of possible frequencies). The mathematics of how we update this prior belief is rooted in Bayes' theorem.''')

st.write('''Click the button to compute the 95\% credible upper bounds on the frequency ratios of each card and obtain a posterior probability of no short prints. Unlike the confidence upper bounds, you can really interpret the 95\% upper confidence bound 
	as the value which you are 95\% sure the true frequency is less than. As before, you can adjust the 95\% to any percentage you 
	want between 70 and 99.9999. The posterior probability of no-short prints is unaffected by this value - you can interpret it as the updated probability of no short prints in this set, based on your 
	prior beliefs.''')

credible_value = st.number_input("Input credible level above 70 and below 100:",key='confidence_3', value=95.0, min_value=70.0, max_value=99.99999, step=0.01,format="%.5f")


#obs: list of observed quantities of each card in the rarity
#Let k be the length of obs (number of distinct cards in rarity)
#Let n be the sum of obs (total number of cards in rarity)
#Let 1_k be the length-k list of 1s.
#Computes beta(1_k)/(beta(1_k+obs)*k^n) in a manner that avoids overflow and minimizes loss of precision.
def beta_quotient(obs):
    k=len(obs)
    n=sum(obs)
    obs.sort(reverse=True)
    diff=[obs[i]-obs[i+1] for i in range(len(obs)-1)]
    ret=1.0
    repeats=1
    curr_repeat=0
    curr=obs[0]
    curr_k=n
    numerator=n+k-1
    walk_down=0
    curr_index=0
    while curr>0:
        if curr_index<len(obs)-1 and walk_down==diff[curr_index]:
            walk_down=0
            curr_index+=1
            repeats+=1
            continue
        for i in range(repeats):
            ret*=numerator/curr
            while ret>k and curr_k>0:
                ret/=k
                curr_k-=1
            numerator-=1
        curr-=1
        walk_down+=1
    while curr_k>0:
        ret/=k
        curr_k-=1
    return ret


def bounds(confidence, prior, obs):
    p=(1-prior)/(1-prior+prior*beta_quotient(obs))
    post=1-p
    k=len(obs)
    n=sum(obs)
    ret=[0]*k
    for i in range(k):
        threshold=p*betainc(1+obs[i], n+k-obs[i]-1, 1/k, out=None)
        if threshold>confidence:
            print('1')
            #get x that solves cumulative =confidence/p
            ret[i]=beta.ppf(confidence/p, 1+obs[i], n+k-obs[i])
        elif threshold+post>confidence:
            print('2')
            ret[i]=1/k
        else:
            print('3')
            #get x that solves cumulative=(confidence-prior)/p
            ret[i]=beta.ppf((confidence-post)/p, 1+obs[i], n+k-obs[i])
    return [x*k for x in ret], post



if st.button('Compute credible bounds'):
	c=credible_value/100
	nums=st.session_state.numbers_2
	distinct=len(nums)
	total=st.session_state.sum_2
	observed_freq=[x/total*distinct for x in nums]
	creds,post=bounds(c,prior/100, nums)
	df = pd.DataFrame({'Observed frequency ratio':observed_freq,  'Credible bound': creds}, index=[f'Card {i+1}' for i in range(distinct)])
	st.table(df)
	st.write(f'Posterior probability of no short prints: {post:.5f}')

#button for credible 
#button to update prior
#display credible upper bound
#display


