import sys 
import csv
import json
import time

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
        
    rem_work_d = [[0]*(N) for _ in range(D)]
        
    for d in range(D-1,-1,-1) :
        for i in range(N) :
            rem_work_d[d][i] = (1 - on_leave[i*D+d])
            if(d+1<D) :
                rem_work_d[d][i] += rem_work_d[d+1][i]

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
    
    for s in bposs :
        if solve(0,0,nurses,m-s,a-s,e,s,surgical_avail[0],max_shifts*N,gen_avail[0],gen_avail[0]+surgical_avail[0],gen_avail[0]+surgical_avail[0],gen_avail[0]+surgical_avail[0],sn) :
            for day in range(D):
                for nurse in range(N):
                    shift = schedule[nurse*D + day]
                    result[f"N{nurse}_{day}"] = shift_int_str[shift] 
            break
                
    with open(output_file, 'w') as f:
        json.dump(result, f)