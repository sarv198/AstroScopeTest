# To-DO

## mission critical (potential impactor)
- orbit map
    - [ ] filters of objects
        - key to prevent lag: max of 10-20 objects
    - [ ] orbit visualization (either simulated or generic orbits)
        - check streams
    - [ ] education: objects have educational pop-up with various statistics when clicked on
        - add a card menu with all currently displayed NEOs

- impact map
    - [ ] bare minimum: map with an affected region indicator
    - [ ] damage factor: assessment of damage
    - [ ] statistics: potential energy, casualties, earthquake magnitude
    - [ ] physics: check chat for physics equations, calculate in backend

## key focuses (near earth objects)
- [ ] add "streams" like WMPGANG
- [ ] add data visualizations via seaborn, streamlit, or matplotlib


## nice to haves (not near earth objects)
- [ ] add gamification mode: potentially have a "draft pick" of different NEOs to maximize the damage factor
- [ ] more advanced animations



## Data Workflow
1. Query Sentry for "High Impact Probability" Objects: obtain des, energy, etc.
2. Use des to query sbdb and cad for more information
3. Process and combine into good format to pass to react frontend