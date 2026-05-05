# Code Record

- TaskSequence
    
    通常順序為
    
    1. TaskSequence.create()
    2. ts.addTask()
    3. dispatch()
    
    EX：一台叉車移動至station舉起2個item的範例code
    
    ```cpp
    TaskSequence ts = TaskSequence.create(forklift, 0, 0);
    ts.addTask(TASKTYPE_TRAVEL, station);
    ts.addTask(TASKTYPE_LOAD, item, station, 2);
    ts.dispatch();
    ```