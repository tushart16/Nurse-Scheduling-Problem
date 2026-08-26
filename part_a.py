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
    
schedule = [-1]*(N*D)
        
avail = [max_shifts]*N
availsm = max_shifts*N
streak = [0]*N
last_shift = [0]*N # not needed? refer from schedule itself

curr_m_left = m
curr_a_left = a
curr_e_left = e
curr_s = 0
curr_unassigned_surg = Ns

#RMAEB, R->0, M->1, A->2, E->3, B->4 , the corresponding bitmask is 2^(i)
def get_shifts(nurse, day) :
    shifts = 1
    #if nurse is on leave or has worked for K consec days or all shifts are consumed then must REST
    if on_leave[nurse*D + day] == 1 or streak[nurse] == 5 or avail[nurse] == 0 : 
        return shifts
    
    #always available to work in E shift
    shifts |= 8
    
    #nurse can work in M or B shift iff prev shift was A or R
    if last_shift[nurse] == 0 or last_shift[nurse] == 2 : 
        shifts |= 2
        if nurse < Ns and avail[nurse] >= 2 and surgical_day[day] == 1:
            shifts |= 16
    
    #nurse can work in A shift iff prev shift was not B
    if last_shift[nurse] != 4 : 
        shifts |= 4
        
    return shifts
    
def solve(day, nurse_idx, nurses_mrv) :
    global curr_m_left, curr_a_left, curr_e_left, curr_s, availsm, curr_unassigned_surg
    
    if nurse_idx == N :
        if curr_m_left == 0 and curr_a_left == 0 and curr_e_left == 0 :
            if surgical_day[day] == curr_s :
                if day == D - 1: 
                    return True
                
                # MRV
                next_nurses_mrv = sorted(range(N), key = lambda i : (get_shifts(i,day+1).bit_count(), i >= Ns)) #same count later
                
                curr_m_left = m
                curr_a_left = a
                curr_e_left = e
                curr_s = 0
                prev_unassigned_surg = curr_unassigned_surg
                curr_unassigned_surg = Ns
                if solve(day+1,0,next_nurses_mrv) :
                    return True
                
                curr_s = surgical_day[day]
                curr_m_left = curr_a_left = curr_e_left = 0
                curr_unassigned_surg = prev_unassigned_surg
                
        return False
    net_shifts_req = (D-1-day)*(m+a+e) + curr_a_left+curr_e_left+curr_m_left
    if availsm < net_shifts_req:
      return False
    if curr_m_left + curr_a_left + curr_e_left > (N-nurse_idx)*(1+surgical_day[day]) :
        return False
    if curr_e_left > N-nurse_idx or curr_a_left > N-nurse_idx or curr_m_left > N-nurse_idx:
        return False 
    curr_unassigned_gen = N-nurse_idx-curr_unassigned_surg
    max_poss = (curr_unassigned_surg*2+ curr_unassigned_gen) if surgical_day[day]==1 else (curr_unassigned_surg+curr_unassigned_gen)
    if max_poss < curr_a_left+curr_e_left+curr_m_left:
      return False
    
    nurse = nurses_mrv[nurse_idx]
    shifts = get_shifts(nurse,day)
    
    checked = 0
    is_surgical = ( 1 if nurse<Ns else 0)
    curr_unassigned_surg -= is_surgical
    #check if surgical day and no surgical nurses yet
    if surgical_day[day] == 1 and curr_s == 0 and curr_m_left > 0 and curr_a_left > 0 and ((shifts >> 4)&1) == 1:
        last = last_shift[nurse]
        
        schedule[nurse*D+day] = 4
        avail[nurse] -= 2
        availsm-=2
        streak[nurse] += 1
        last_shift[nurse] = 4
        
        curr_m_left -= 1
        curr_a_left -= 1
        curr_s = 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        checked |= 16
        curr_s = 0
        curr_a_left += 1
        curr_m_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 2
        availsm+=2
        schedule[nurse*D+day] = -1
        
    # LCV
    # checking if R can be assigned
    if (N-1-nurse_idx >= curr_e_left) and (N-1-nurse_idx-curr_e_left)*(1+surgical_day[day]) >= curr_m_left + curr_a_left :
        prev = streak[nurse]
        last = last_shift[nurse]
        
        schedule[nurse*D+day] = 0
        streak[nurse] = 0
        last_shift[nurse] = 0
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        last_shift[nurse] = last
        streak[nurse] = prev
        schedule[nurse*D+day] = -1
    
    # can never rest now
    if curr_e_left >= max(curr_m_left,curr_a_left) and curr_e_left > 0 and ((shifts >> 3)&1) == 1 :
        last = last_shift[nurse]
        
        schedule[nurse*D+day] = 3
        avail[nurse] -= 1
        availsm-=1
        streak[nurse] += 1
        last_shift[nurse] = 3
        
        curr_e_left -= 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        checked |= 8
        curr_e_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 1
        availsm+=1
        schedule[nurse*D+day] = -1
    
    if N-nurse_idx-curr_e_left < curr_m_left + curr_a_left and (curr_m_left == 0 or curr_a_left == 0) :
      curr_unassigned_surg+= is_surgical
      return False
    if N-nurse_idx-curr_e_left < curr_m_left + curr_a_left and curr_m_left > 0 and curr_a_left > 0 :
        if surgical_day[day] == 0 :
            curr_unassigned_surg+= is_surgical
            return False
        
        if ((shifts >> 4)&1) == 1 and ((checked >> 4)&1) == 0 :
            last = last_shift[nurse]
            prev = curr_s
            
            schedule[nurse*D+day] = 4
            avail[nurse] -= 2
            availsm-=2
            streak[nurse] += 1
            last_shift[nurse] = 4
            
            curr_m_left -= 1
            curr_a_left -= 1
            curr_s = 1
            
            if(solve(day,nurse_idx+1,nurses_mrv)) : 
                return True
            
            curr_s = prev
            curr_a_left += 1
            curr_m_left += 1
            
            checked |= 16
            
            last_shift[nurse] = last
            streak[nurse] -= 1
            avail[nurse] += 2
            availsm+=2
            schedule[nurse*D+day] = -1
        
    if curr_a_left >= curr_m_left and curr_a_left > 0 and ((shifts >> 2)&1) == 1 :
        last = last_shift[nurse]
        
        schedule[nurse*D+day] = 2
        avail[nurse] -= 1
        availsm-=1
        streak[nurse] += 1
        last_shift[nurse] = 2
        
        curr_a_left -= 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        checked |= 4
        curr_a_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 1
        availsm+=1
        schedule[nurse*D+day] = -1
    
    # M
    if((shifts >> 1)&1) == 1 and curr_m_left > 0 :
        last = last_shift[nurse]
            
        schedule[nurse*D+day] = 1
        avail[nurse] -= 1
        availsm-=1
        streak[nurse] += 1
        last_shift[nurse] = 1
        
        curr_m_left -= 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        curr_m_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 1
        availsm+=1
        schedule[nurse*D+day] = -1
    
    # A
    if((shifts >> 2)&1) == 1 and curr_a_left > 0 and ((checked >> 2)&1) == 0 :
        last = last_shift[nurse]
        
        schedule[nurse*D+day] = 2
        avail[nurse] -= 1
        availsm-=1
        streak[nurse] += 1
        last_shift[nurse] = 2
        
        curr_a_left -= 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        checked |= 4
        curr_a_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 1
        availsm+=1
        schedule[nurse*D+day] = -1
        
    # E
    if((shifts >> 3)&1) == 1 and curr_e_left > 0 and ((checked >> 3)&1) == 0 :
        last = last_shift[nurse]
        
        schedule[nurse*D+day] = 3
        avail[nurse] -= 1
        availsm-=1
        streak[nurse] += 1
        last_shift[nurse] = 3
        
        curr_e_left -= 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        checked |= 8
        curr_e_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 1
        availsm+=1
        schedule[nurse*D+day] = -1
    
    # B
    if ((shifts >> 4)&1) == 1 and curr_m_left > 0 and curr_a_left > 0 and ((checked >> 4)&1) == 0 :
        last = last_shift[nurse]
        prev = curr_s
        
        schedule[nurse*D+day] = 4
        avail[nurse] -= 2
        availsm-=2
        streak[nurse] += 1
        last_shift[nurse] = 4
        
        curr_m_left -= 1
        curr_a_left -= 1
        curr_s = 1
        
        if(solve(day,nurse_idx+1,nurses_mrv)) : 
            return True
        
        checked |= 16
        curr_s = prev
        curr_a_left += 1
        curr_m_left += 1
        
        last_shift[nurse] = last
        streak[nurse] -= 1
        avail[nurse] += 2
        availsm+=2
        schedule[nurse*D+day] = -1
        
    curr_unassigned_surg+= is_surgical
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
    
    output_file = sys.argv[2]
    result = {}
    start_time = time.time()
    if solve(0,0,nurses) :
        end_time=time.time()
        print(end_time-start_time)
        for day in range(D):
            for nurse in range(N):
                shift = schedule[nurse*D + day]
                result[f"N{nurse}_{day}"] = shift_int_str(shift)      
    with open(output_file, 'w') as f:
        json.dump(result, f)