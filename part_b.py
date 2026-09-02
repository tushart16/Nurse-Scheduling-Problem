import sys 
import csv
import json
import time
import random

sys.setrecursionlimit(10000)

#RMAEB, R->0, M->1, A->2, E->3, B->4 , the corresponding bitmask is 2^(i)
def get_shifts(nurse, day) :
    shifts = 1
    #if nurse is on leave or has worked for 5 consec days or all shifts are consumed then must REST
    if on_leave[nurse*D + day] == 1 or streak[nurse] == 5 or avail[nurse] == 0 : 
        return shifts
    
    if day == 0 :
        shifts |= 2
        shifts |= 4
        shifts |= 8
        
        if nurse < Ns and avail[nurse] >= 2 and surgical_day[day] == 1:
            shifts |= 16
        return shifts

    #always available to work in E shift
    shifts |= 8
    
    #nurse can work in M or B shift iff prev shift was A or R
    if schedule[nurse*D + day-1] == 0 or schedule[nurse*D + day-1] == 2 : 
        shifts |= 2
        if nurse < Ns and avail[nurse] >= 2 and surgical_day[day] == 1:
            shifts |= 16
    
    #nurse can work in A shift iff prev shift was not B
    if schedule[nurse*D + day-1] != 4 : 
        shifts |= 4
        
    return shifts
    
def solve(day, nurse_idx, nurses_mrv, curr_m_left, curr_a_left, curr_e_left, curr_b_left, curr_surg_left, avail_shifts_sum, curr_gen_left, offer_m, offer_a, offer_e, offer_b) :    
    if nurse_idx == N :
        if curr_m_left == 0 and curr_a_left == 0 and curr_e_left == 0 and curr_b_left == 0 :
            if day == D - 1: 
                return True
            
            many = [get_shifts(i,day+1) for i in range(N)]
            
            can_e,can_a,can_m,can_b = 0,0,0,0
            for i in range(N) :
                shifts = many[i]
                if(shifts&16) : can_b+=1
                elif(shifts&2) : can_m+=1
                elif(shifts&4) : can_a+=1
                elif(shifts&8) : can_e+=1
                
            if can_e+can_a+can_m+can_b < e or can_a+can_m+can_b<a or can_m+can_b<m :
                return False

            surg_cap = sum(avail[i]//2 for i in range(Ns))
            if surg_cap < rem_surg_d[day+1]:
                return False
            
            next = sorted(range(N), key=lambda i: (-avail[i]))
            
            next_offer_b = can_b
            next_offer_m = can_b+can_m
            next_offer_a = can_b+can_m+can_a
            next_offer_e = can_b+can_m+can_a+can_e
            
            if surgical_day[day+1] == 0 :
                if solve(day+1,0,next,m,a,e,0,surgical_avail[day+1],avail_shifts_sum,gen_avail[day+1],next_offer_m,next_offer_a,next_offer_e,next_offer_b) :
                    return True
            else :
                for s in range(1,min(m,a,Ns,can_b)+1) :
                    if solve(day+1,0,next,m-s,a-s,e,s,surgical_avail[day+1],avail_shifts_sum,gen_avail[day+1],next_offer_m,next_offer_a,next_offer_e,next_offer_b) :
                        return True
                    
                
        return False
    
    nurse = nurses_mrv[nurse_idx]
    
    not_on_leave = 1-on_leave[nurse*D + day]
    is_surgical = (nurse<Ns)
    is_general = (nurse>=Ns)
    total_nurses = curr_surg_left + curr_gen_left
    
    next_curr_surg_left = curr_surg_left - (is_surgical)*(not_on_leave)
    next_curr_gen_left = curr_gen_left - (is_general)*(not_on_leave)
    shifts = get_shifts(nurse,day)
    
    next_offer_m = offer_m - ((shifts&2) != 0) 
    next_offer_a = offer_a - ((shifts&4) != 0)
    next_offer_e = offer_e - ((shifts&8) != 0)
    next_offer_b = offer_b - ((shifts&16) != 0)
        
    net_shifts_req = (D-1-day)*(m+a+e) + curr_m_left+curr_a_left+curr_e_left+2*curr_b_left
    if avail_shifts_sum < net_shifts_req:
        return False
    
    if curr_m_left > total_nurses or curr_a_left > total_nurses or curr_e_left > total_nurses or curr_b_left > curr_surg_left:
        return False
    
    if offer_m < curr_m_left or offer_a < curr_a_left or offer_e < curr_e_left or offer_b < curr_b_left :
        return False
    
    if total_nurses < (curr_m_left + curr_a_left + curr_e_left + curr_b_left) :
        return False
        
    check_shifts = []
        
    if not_on_leave == 1 :
        if (shifts&16) and curr_b_left > 0:
            check_shifts.append(4)
        if (shifts&2) and curr_m_left > 0:
            check_shifts.append(1)
        if (shifts&4) and curr_a_left > 0:
            check_shifts.append(2)
        if (shifts&8) and curr_e_left > 0:
            check_shifts.append(3)
                                    
        if total_nurses - 1 >= curr_m_left + curr_a_left + curr_e_left + curr_b_left:
            check_shifts.append(0)
    else :
        check_shifts.append(0) 
    
    for s in check_shifts :
        prev_streak = streak[nurse]
        schedule[nurse*D + day] = s
        
        next_avail_shifts_sum = avail_shifts_sum
        next_curr_m_left = curr_m_left
        next_curr_a_left = curr_a_left
        next_curr_e_left = curr_e_left
        next_curr_b_left = curr_b_left
        
        if s == 0 :
            streak[nurse] = 0
        else :
            avail[nurse] -= 1
            next_avail_shifts_sum -= 1
            streak[nurse] += 1
            if s == 1 :
                next_curr_m_left -= 1
            elif s == 2 :
                next_curr_a_left -= 1
            elif s == 3 :
                next_curr_e_left -= 1
            else :
                next_curr_b_left -= 1
                avail[nurse] -= 1
                next_avail_shifts_sum -= 1
    
        if(solve(day,nurse_idx+1,nurses_mrv,next_curr_m_left,next_curr_a_left,next_curr_e_left,next_curr_b_left,next_curr_surg_left,next_avail_shifts_sum,next_curr_gen_left,next_offer_m,next_offer_a,next_offer_e,next_offer_b)) : 
            return True
        
        avail[nurse] += (s != 0) + (s == 4)
        schedule[nurse*D + day] = -1
        streak[nurse] = prev_streak
        
    return False

def get_cost(count_m, count_a, count_e) :
    return 3*(count_m*count_m + count_a*count_a + count_e*count_e) - (count_m + count_a + count_e)**2

def total_cost() :
    cost = 0
    for i in range(N) :
        cost += get_cost(nurse_m[i],nurse_a[i],nurse_e[i])
    
    return cost

def allowed(s1, s2) :
    if s2 == 0 or s2 == 3 :
        return True
    if s2 == 1 or s2 == 4 :
        return ((s1 == 2) or (s1 == 0)) 
    return (s1 != 4)

def verify_streak(n,day,s) :
    if s == 0 :
        return True
    
    left, right = 0,0
    for d in range(day-1,-1,-1) :
        if schedule[n*D + d] != 0 :
            left += 1
        else: break
            
        
    for d in range(day+1, D):
        if schedule[n*D + d] != 0 :
            right += 1
        else: break
        
    return (left+1+right) <= 5

def valid(n,d,s1,s2) :
    if s1 == s2 :
        return False
    if s2 != 0 and on_leave[n*D + d] :
        return False
    if s2 == 4 and n >= Ns: 
        return False
    
    slots_change = (s2 != 0) + (s2 == 4) - (s1 != 0) - (s1 == 4)
    
    if nurse_k[n] + slots_change > max_shifts : 
        return False
    
    if d > 0 and not allowed(schedule[n*D+d-1], s2) : 
        return False
    if d < D - 1 and not allowed(s2, schedule[n*D+d+1]) :
        return False
    
    if s1 == 0 and s2 != 0 and not verify_streak(n, d, s2) :
        return False
    return True

def restart() :
    swaps = 4
    tried = 0
    while swaps > 0 and tried < 120 :
        tried += 1
        d = random.randint(0,D-1)
        n1,n2 = random.sample(range(N),2)
        s = schedule[n1*D+d]
        s2 = schedule[n2*D+d]
        if s != s2 and valid(n1,d,s,s2) and valid(n2,d,s2,s) :
            swaps -= 1
            
            new_m1 = nurse_m[n1] - (1 if s in (1,4) else 0) + (1 if s2 in (1,4) else 0)
            new_a1 = nurse_a[n1] - (1 if s in (2,4) else 0) + (1 if s2 in (2,4) else 0)
            new_e1 = nurse_e[n1] - (s == 3) + (s2 == 3)
            new_m2 = nurse_m[n2] - (1 if s2 in (1,4) else 0) + (1 if s in (1,4) else 0)
            new_a2 = nurse_a[n2] - (1 if s2 in (2,4) else 0) + (1 if s in (2,4) else 0)
            new_e2 = nurse_e[n2] - (s2 == 3) + (s == 3)
            
            schedule[n1*D + d] = s2
            schedule[n2*D + d] = s
            nurse_m[n1], nurse_a[n1] , nurse_e[n1] = new_m1,new_a1,new_e1
            nurse_m[n2], nurse_a[n2] , nurse_e[n2] = new_m2,new_a2,new_e2
            nurse_k[n1] += (s2 != 0) + (s2 == 4) - (s != 0) - (s == 4)
            nurse_k[n2] += (s != 0) + (s == 4) - (s2 != 0) - (s2 == 4)
            
            

def local_search() :
    for n in range(N) :
        for d in range(D) :
            s = schedule[n*D + d]
            nurse_m[n] += (s == 1) + (s == 4)
            nurse_a[n] += (s == 2) + (s == 4)
            nurse_e[n] += (s == 3)
            nurse_k[n] += (s != 0) + (s == 4)
    
    current_cost = total_cost()
    best_cost = current_cost
    best_schedule = list(schedule)
    
    flat_max = 100
    flat_count = 0
    bad_max = 3000
    bad_count = 0
        
    while time.time()-start_time < 2 :
        if best_cost == 0 :
            break
        
        if flat_count >= flat_max or bad_count >= bad_max :
            restart()
            current_cost = total_cost()
            flat_count = 0
            bad_count = 0
            continue
        
        d = random.randint(0,D-1)    
        nurse_1 = max(random.sample(range(N),min(4,N)), key = lambda i : get_cost(nurse_m[i],nurse_a[i],nurse_e[i]))
        s = schedule[nurse_1*D + d]
        
        nurse_2 = [i for i in range(N) if i != nurse_1 and schedule[i*D+d] != s]
        if not nurse_2 :
            bad_count += 1
            continue
        
        nurse_2 = random.choice(nurse_2)
        s2 = schedule[nurse_2*D + d]
        
        if valid(nurse_1,d,s,s2) and valid(nurse_2,d,s2,s) :
            prev_cost = get_cost(nurse_m[nurse_2],nurse_a[nurse_2],nurse_e[nurse_2]) + get_cost(nurse_m[nurse_1],nurse_a[nurse_1],nurse_e[nurse_1])
            new_m1 = nurse_m[nurse_1] - (1 if s in (1,4) else 0) + (1 if s2 in (1,4) else 0)
            new_a1 = nurse_a[nurse_1] - (1 if s in (2,4) else 0) + (1 if s2 in (2,4) else 0)
            new_e1 = nurse_e[nurse_1] - (s == 3) + (s2 == 3)
            new_m2 = nurse_m[nurse_2] - (1 if s2 in (1,4) else 0) + (1 if s in (1,4) else 0)
            new_a2 = nurse_a[nurse_2] - (1 if s2 in (2,4) else 0) + (1 if s in (2,4) else 0)
            new_e2 = nurse_e[nurse_2] - (s2 == 3) + (s == 3)
            new_cost = get_cost(new_m2,new_a2,new_e2) + get_cost(new_m1,new_a1,new_e1)
            diff = new_cost-prev_cost
            
            if diff <= 0:
                schedule[nurse_1*D + d] = s2
                schedule[nurse_2*D + d] = s
                nurse_m[nurse_1], nurse_a[nurse_1] , nurse_e[nurse_1] = new_m1,new_a1,new_e1
                nurse_m[nurse_2], nurse_a[nurse_2] , nurse_e[nurse_2] = new_m2,new_a2,new_e2
                nurse_k[nurse_1] += (s2 != 0) + (s2 == 4) - (s != 0) - (s == 4)
                nurse_k[nurse_2] += (s != 0) + (s == 4) - (s2 != 0) - (s2 == 4)
                current_cost += diff
                
                if diff < 0 :
                    
                    flat_count = 0
                    bad_count = 0
                    
                    if current_cost < best_cost :
                        best_cost = current_cost
                        best_schedule = list(schedule)
                else :
                    flat_count += 1
                    bad_count = 0
            else :
                bad_count += 1                
        else :
            bad_count += 1
            
    for i in range(N*D) :
        schedule[i] = best_schedule[i]
                
def parse_input(input_csv):
    """Reads the CSV and initializes problem variables."""
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        row = next(reader)
        print(row)
    
        N = int(row['N'])
        D = int(row['D'])
        N_s = int(row['N_s'])
        N_g = int(row['N_g'])
        m = int(row['m'])
        a = int(row['a'])
        e = int(row['e'])
        T = float(row['T'])
        days = row['days']
        max_shifts = int(row['K'])
        leaves = row['leaves']
    return N, D, N_s, N_g, m, a, e, T, days, max_shifts, leaves
if __name__ == '__main__': 
       
    N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves = parse_input(sys.argv[1])
    output_file = sys.argv[2]
    
    surgical_day = [1 if d == 'S' else 0 for d in days]
    on_leave = [1 if a == 'L' else 0 for a in leaves]
    surgical_avail = [Ns]*D
    gen_avail = [Ng]*D
    schedule = [-1]*(N*D)
    
    rem_surg_d = [0]*D
    count = 0
    for d in range(D-1,-1,-1) :
        count += (surgical_day[d] == 1)
        rem_surg_d[d] = count

    avail = [max_shifts]*N
    streak = [0]*N 
    
    nurses = sorted(range(N), key=lambda i: (-avail[i]))
    
    sn = 0
    for n in range(0,Ns) :
        if surgical_day[0] == 1 and avail[n] >= 2 : sn += 1
        for d in range(0,D) :
            surgical_avail[d] -= on_leave[n*D+d]
            
    for n in range(Ns,N) :
        for d in range(0,D) :
            gen_avail[d] -= on_leave[n*D+d]

    result = {}
    start_time = time.time()
    
    bposs = range(1,min(m,a,Ns)+1) if surgical_day[0] else [0] 
        
    shift_int_str = ['R','M','A','E','B']
    
    found = False
    
    for s in bposs :
        if solve(0,0,nurses,m-s,a-s,e,s,surgical_avail[0],max_shifts*N,gen_avail[0],gen_avail[0]+surgical_avail[0],gen_avail[0]+surgical_avail[0],gen_avail[0]+surgical_avail[0],sn) :
            found = True
            break
    
    nurse_m = [0]*N
    nurse_a = [0]*N
    nurse_e = [0]*N
    nurse_k = [0]*N
    if found :
        local_search()
        for day in range(D):
            for nurse in range(N):
                shift = schedule[nurse*D + day]
                result[f"N{nurse}_{day}"] = shift_int_str[shift] 
                
    with open(output_file, 'w') as f:
        json.dump(result, f)