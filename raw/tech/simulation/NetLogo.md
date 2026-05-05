# NetLogo

---

# Links

---

**both-ends：針對link，回傳兩個端點的turtle**

`links`

```lisp
crt 2
ask turtle 0 [ create-link-with turtle 1 ]
ask link 0 1 [
  ask both-ends [ set color red ] ;; turtles 0 and 1 both turn red
]
```