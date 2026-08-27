import sys 
import csv
import json
import time

sys.setrecursionlimit(2500)

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

N, D, Ns, Ng, m, a, e, T, days, max_shifts, leaves = parse_input(sys.argv[1])

surgical_day = [1 if d == 'S' else 0 for d in days]
on_leave = [1 if a == 'L' else 0 for a in leaves]
surgical_avail = [Ns]*D
gen_avail = [Ng]*D
schedule = [-1]*(N*D)

avail = [max_shifts]*N
streak = [0]*N

#RMAEB, R->0, M->1, A->2, E->3, B->4 , the corresponding bitmask is 2^(i)
def get_shifts(nurse, day) :
    shifts = 1
    #if nurse is on leave or has worked for K consec days or all shifts are consumed then must REST
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
    
def solve(day, nurse_idx, nurses_mrv, curr_m_left, curr_a_left, curr_e_left, curr_s, curr_surg_left, avail_shifts_sum, curr_gen_left) :    
    if nurse_idx == N :
        if curr_m_left == 0 and curr_a_left == 0 and curr_e_left == 0 :
            if surgical_day[day] == curr_s :
                if day == D - 1: 
                    return True
                
                next = sorted(range(N), key=lambda i: (get_shifts(i, day+1).bit_count(), i >= Ns))
                
                if solve(day+1,0,next,m,a,e,0,surgical_avail[day+1],avail_shifts_sum,gen_avail[day+1]) :
                    return True
                
        return False
    
    if curr_m_left == 0 and curr_a_left == 0 and curr_e_left == 0 :
        if surgical_day[day] == 1 and curr_s == 0 :
            return False
        
        nurse = nurses_mrv[nurse_idx]
        prev_streak = streak[nurse]
        schedule[nurse*D + day] = 0
        streak[nurse] = 0
        next_curr_surg_left = curr_surg_left - (nurse < Ns)*(1-on_leave[nurse*D + day])
        next_curr_gen_left = curr_gen_left - (nurse >= Ns)*(1-on_leave[nurse*D + day])
        if solve(day,nurse_idx+1,nurses_mrv,0,0,0,curr_s,next_curr_surg_left,avail_shifts_sum,next_curr_gen_left) :
            return True
        else :
            schedule[nurse*D + day] = -1
            streak[nurse] = prev_streak
            return False
    
    net_shifts_req = (D-1-day)*(m+a+e) + curr_a_left+curr_e_left+curr_m_left
    if avail_shifts_sum < net_shifts_req:
        return False
    
    total_nurses = curr_surg_left + curr_gen_left
    if curr_m_left > total_nurses or curr_a_left > total_nurses or curr_e_left > total_nurses:
        return False
     
    nurse = nurses_mrv[nurse_idx]
    if curr_a_left+curr_e_left+curr_m_left > (curr_surg_left*(1+surgical_day[day])+ curr_gen_left) :
        return False
  
    if surgical_day[day] == 1 and curr_s == 0 and curr_surg_left == 0:
        return False
    
    if total_nurses-curr_e_left < curr_m_left + curr_a_left and (curr_m_left == 0 or curr_a_left == 0 or surgical_day[day] == 0 or curr_surg_left == 0) :
        return False
    
    shifts = get_shifts(nurse,day)
    check_shifts = []
    
    ev_slots = min(curr_gen_left+(nurse<Ns)*(1-on_leave[nurse*D + day]),curr_e_left)
    surg_nurse_ma = curr_surg_left - (nurse<Ns)*(1-on_leave[nurse*D + day]) - (curr_e_left-ev_slots)
    ma_slots = (curr_gen_left+(nurse<Ns)*(1-on_leave[nurse*D + day]) - ev_slots) + surg_nurse_ma*(1+surgical_day[day])
    #check if surgical day and no surgical nurses yet or need it to fulfill slots
    if surgical_day[day] == 1 and (curr_s == 0 or ma_slots < curr_m_left + curr_a_left) and curr_m_left > 0 and curr_a_left > 0 and (shifts&16) :                
        check_shifts.append(4)
       
    # R 
    ev_slots = min(curr_gen_left-(nurse>=Ns)*(1-on_leave[nurse*D + day]),curr_e_left)
    surg_nurse_ma = curr_surg_left - (nurse<Ns)*(1-on_leave[nurse*D + day]) - (curr_e_left-ev_slots)
    ma_slots = (curr_gen_left - (nurse>=Ns)*(1-on_leave[nurse*D + day]) - ev_slots) + surg_nurse_ma*(1+surgical_day[day])
    if (total_nurses - (1-on_leave[nurse*D + day]) >= curr_e_left) and ma_slots >= curr_m_left + curr_a_left :
        check_shifts.append(0)
        
    if curr_e_left >= max(curr_m_left, curr_a_left) :
        if (shifts&8) :
            check_shifts.append(3)
        if curr_a_left >= curr_m_left :
            if (shifts&4) :
                check_shifts.append(2)
            if (shifts&2) :
                check_shifts.append(1)
        else :
            if (shifts&2) :
                check_shifts.append(1)
            if (shifts&4) :
                check_shifts.append(2)
    elif curr_a_left >= max(curr_m_left, curr_e_left) :
        if (shifts&4) :
            check_shifts.append(2)
        if curr_e_left >= curr_m_left :
            if (shifts&8) :
                check_shifts.append(3)
            if (shifts&2) :
                check_shifts.append(1)
        else :
            if (shifts&2) :
                check_shifts.append(1)
            if (shifts&8) :
                check_shifts.append(3)
    else :
        if (shifts&2) :
            check_shifts.append(1)
        if curr_e_left >= curr_a_left :
            if (shifts&8) :
                check_shifts.append(3)
            if (shifts&4) :
                check_shifts.append(2)
        else :
            if (shifts&4) :
                check_shifts.append(2)
            if (shifts&8) :
                check_shifts.append(3)
            
        
    if 4 not in check_shifts and (shifts&16) and curr_m_left > 0 and curr_a_left > 0 :
        check_shifts.append(4)
    
    for s in check_shifts :
        prev_streak = streak[nurse]
        schedule[nurse*D + day] = s
        
        next_curr_surg_left = curr_surg_left - (nurse < Ns)*(1-on_leave[nurse*D + day])
        next_curr_gen_left = curr_gen_left - (nurse >= Ns)*(1-on_leave[nurse*D + day])
        
        next_avail_shifts_sum = avail_shifts_sum
        next_curr_m_left = curr_m_left
        next_curr_a_left = curr_a_left
        next_curr_e_left = curr_e_left
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
                next_curr_m_left -= 1
                next_curr_a_left -= 1
                avail[nurse] -= 1
                next_avail_shifts_sum -= 1

        next_curr_s = curr_s
        if s == 4 :
            next_curr_s = 1
    
        if(solve(day,nurse_idx+1,nurses_mrv,next_curr_m_left,next_curr_a_left,next_curr_e_left,next_curr_s,next_curr_surg_left,next_avail_shifts_sum,next_curr_gen_left)) : 
            return True
        
        avail[nurse] += (s != 0) + (s == 4)
        schedule[nurse*D + day] = -1
        streak[nurse] = prev_streak
        
    return False
    

def shift_int_str(s) :
    if s == 0 :
        return 'R'
    elif s == 1 :
        return 'M' 
    elif s == 2 :
        return 'A'
    elif s == 3 :
        return 'E'
    else :
        return 'B'
    
if __name__ == '__main__':     
    nurses = [i for i in range(N)]
    
    for n in range(0,Ns) :
        for d in range(0,D) :
            surgical_avail[d] -= on_leave[n*D+d]
            
    for n in range(Ns,N) :
        for d in range(0,D) :
            gen_avail[d] -= on_leave[n*D+d]

    output_file = sys.argv[2]
    result = {}
    start_time = time.time()
    if solve(0,0,nurses,m,a,e,0,surgical_avail[0],max_shifts*N,gen_avail[0]) :
        end_time=time.time()
        print(end_time-start_time)
        for day in range(D):
            for nurse in range(N):
                shift = schedule[nurse*D + day]
                result[f"N{nurse}_{day}"] = shift_int_str(shift)      
    with open(output_file, 'w') as f:
        json.dump(result, f)