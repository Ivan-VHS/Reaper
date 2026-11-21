#!/usr/bin/env python3
"""CSR-120: clinical-principle-inspired software reliability diagnostics.
Engineering heuristics only; this is not a medical or clinical decision system.
"""
import argparse, json, math, sys
from datetime import datetime, timezone

NAMES = """Poiseuille flow capacity|Frank-Starling load response|Laplace wall stress|Flow autoregulation|Fick transport|Bernoulli pressure shift|Fahraeus-Lindqvist narrow-channel flow|Demand hyperemia|Flow shunting|Venous return|Shock resource redistribution|Compensatory tachycardia|Pulse pressure|Hydraulic surge|Low-pressure channel collapse|All-or-none activation|Refractory period|Weber-Fechner response|Stevens response curve|Lateral inhibition|Connection plasticity|Synaptic delay|Pacemaker rhythm|Neurogenic collapse|Excitation threshold|Signal summation|Sensor adaptation|Phantom signal|Error feedback|Clock desynchronization|Homeostasis|Basal metabolism|Catabolism and anabolism|Insulin storage loop|Low-resource failure|Thermoregulation|Setpoint shift|Capacity debt|Buffer effect|Fast-cache depletion|Balance disruption|Circadian cycle|Autophagy|Idle degradation|Data obesity|Self/non-self recognition|Primary and secondary response|Acute isolation response|Chronic unresolved fault|Defensive cascade|False-positive self-attack|Control-plane deficiency|Threat memory|Incubation period|False-positive alarm|Detector evasion|Perimeter barrier|Segment regeneration|Rigid fallback scar|Propagation and herd protection|Therapeutic window|Mass-action response|Half-life|Cumulative overload|Load tolerance|Withdrawal instability|First-pass filtering|Side effects|Module interaction|Effective availability|Gradual tuning|Background clearance|Central processor toxicity|UX placebo response|UX nocebo response|Configuration expression|Mutation and drift|Fault-process apoptosis|Unbounded replication|Fault metastasis|Lifecycle limit|Module senescence|Contextual activation|Latent defect|Pleiotropic parameter|Compensatory scaling|Damage accumulation|Clonal selection|Initialization defect|Integrity repair|Pareto fault concentration|Occam diagnosis|Hickam multiple faults|Detector sensitivity|Detector specificity|Predictive value|Iatrogenic change|Subclinical degradation|Incident history|Differential diagnosis|Symptom suppression|Root-cause correction|Trigger and substrate|Intervention window|Degraded-service mode|Signal projection|Alarm adaptation|Cross-module referred fault|Over-polling|Heartbeat apnea|Emergency prioritization|Chronic overload|Sleep and consolidation|Maintenance deprivation|Operator overload|Tunnel vision|Perception-response conflict|Periodic resonance|Load compensation|Recovery reserve""".split("|")
RANGES=[("transport",1,15),("signals",16,30),("homeostasis",31,45),("defense",46,60),("dosing",61,75),("lifecycle",76,90),("diagnostics",91,105),("operator",106,120)]
CATALOG=[{"id":f"CSR-{i:03d}","name":n,"domain":next(d for d,a,b in RANGES if a<=i<=b)} for i,n in enumerate(NAMES,1)]
# Defaults are generic software thresholds; provide a "thresholds" map to override.
CHECKS=[
("CSR-001","throughput_utilization","max",.90,"Transport saturation; inspect capacity and bottlenecks","warning"),
("CSR-002","queue_depth","max",100,"Queue growth; offered load may exceed service capacity","warning"),
("CSR-003","pressure_ratio","max",1.5,"Pressure stress; inspect downstream resistance and limits","critical"),
("CSR-004","throughput_utilization","max",.85,"Autoregulation margin is shrinking","warning"),
("CSR-011","cpu_utilization","max",.95,"Prioritize critical work and shed noncritical load","critical"),
("CSR-017","retry_rate","max",.10,"Retry amplification; apply bounded exponential backoff","warning"),
("CSR-022","p99_latency_ms","max",1000,"Accumulated hop latency exceeds response budget","warning"),
("CSR-030","clock_skew_ms","max",50,"Subsystem clocks may be losing synchronization","critical"),
("CSR-031","error_rate","max",.01,"Homeostasis deviation: error rate exceeds baseline","warning"),
("CSR-035","available_memory_ratio","min",.10,"Low resource reserve; shed noncritical work","critical"),
("CSR-036","temperature_c","max",85,"Thermal limit approached; reduce load and inspect cooling","critical"),
("CSR-038","sustained_overload_minutes","max",15,"Sustained overload creates recovery debt","warning"),
("CSR-040","cache_hit_ratio","min",.20,"Fast working set may be depleted or poorly sized","warning"),
("CSR-045","storage_growth_ratio","max",.20,"Unbounded data growth; inspect retention and cleanup","warning"),
("CSR-049","unresolved_incidents","max",5,"Chronic unresolved faults are accumulating","warning"),
("CSR-050","alert_rate_per_min","max",60,"Alert cascade; deduplicate and rate-limit notifications","critical"),
("CSR-052","control_coverage","min",.95,"Protection coverage is below target","critical"),
("CSR-055","false_positive_rate","max",.10,"False alarms are degrading signal quality","warning"),
("CSR-063","stale_data_age_s","max",300,"Telemetry freshness exceeded its configured budget","warning"),
("CSR-064","retry_rate","max",.20,"Retries are accumulating faster than work clears","critical"),
("CSR-068","collateral_error_rate","max",.02,"Intervention is affecting adjacent components","warning"),
("CSR-077","config_drift_count","max",0,"Configuration drift detected against declared baseline","warning"),
("CSR-079","process_count_growth_ratio","max",.25,"Unbounded process or worker growth suspected","critical"),
("CSR-087","integrity_failures","max",0,"Integrity failures require investigation","critical"),
("CSR-098","health_score","min",.60,"Subclinical degradation; inspect leading indicators","warning"),
("CSR-099","recent_change_count","max",20,"Correlate incident onset with recent changes","info"),
("CSR-101","restart_count","max",3,"Repeated restarts may mask an unresolved root cause","warning"),
("CSR-104","recovery_budget_ratio","min",.20,"Intervention reserve is low; prefer reversible actions","warning"),
("CSR-105","service_capacity_ratio","min",.50,"Degraded-service mode may preserve core functions","warning"),
("CSR-107","alert_ack_latency_s","max",300,"Alarm habituation or delayed response suspected","warning"),
("CSR-110","heartbeat_gap_s","max",30,"Heartbeat gap; verify scheduler and service liveness","critical"),
("CSR-112","sustained_cpu_minutes","max",30,"Chronic resource pressure; plan recovery and capacity review","warning"),
("CSR-114","maintenance_age_hours","max",720,"Maintenance window overdue; schedule safe housekeeping","info"),
("CSR-115","active_alerts","max",25,"Operator cognitive load is high; group and prioritize alerts","warning"),
("CSR-118","gc_pause_p99_ms","max",500,"Periodic workload resonance may cause latency spikes","warning"),
("CSR-120","recovery_reserve_ratio","min",.20,"Recovery reserve is below target","warning")]
def assess(payload):
    if not isinstance(payload,dict): raise ValueError("Input must be a JSON object")
    metrics=payload.get("metrics",payload); thresholds=payload.get("thresholds",{})
    if not isinstance(metrics,dict) or not isinstance(thresholds,dict): raise ValueError("metrics and thresholds must be JSON objects")
    findings=[]
    for pid,key,op,default,message,severity in CHECKS:
        if key not in metrics: continue
        val=metrics[key]; limit=thresholds.get(key,default)
        if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val):
            findings.append({"principle":pid,"metric":key,"severity":"invalid","message":"Metric must be a finite number"}); continue
        if isinstance(limit,bool) or not isinstance(limit,(int,float)) or not math.isfinite(limit): raise ValueError(f"Invalid threshold: {key}")
        if val>limit if op=="max" else val<limit:
            findings.append({"principle":pid,"metric":key,"value":val,"operator":op,"threshold":limit,"severity":severity,"message":message})
    rank={"critical":0,"invalid":0,"warning":1,"info":2}; findings.sort(key=lambda x:rank.get(x["severity"],3))
    return {"schema":"csr-120/v1","generated_at":datetime.now(timezone.utc).isoformat(),"principle_count":len(CATALOG),"executable_check_count":len(CHECKS),"metrics_evaluated":len(metrics),"status":"critical" if any(x["severity"] in ("critical","invalid") for x in findings) else "attention" if findings else "healthy","findings":findings,"disclaimer":"Engineering heuristics only; not medical advice or clinical diagnostics."}
def main(argv=None):
    p=argparse.ArgumentParser(description="CSR-120 reliability assessment")
    p.add_argument("input",nargs="?",help="JSON telemetry file; stdin if omitted"); p.add_argument("--catalog",action="store_true"); p.add_argument("--pretty",action="store_true")
    a=p.parse_args(argv)
    try:
        if a.catalog: out={"schema":"csr-120/v1","principles":CATALOG,"executable_check_count":len(CHECKS)}
        else:
            raw=open(a.input,encoding="utf-8").read() if a.input else sys.stdin.read()
            out=assess(json.loads(raw))
        print(json.dumps(out,ensure_ascii=False,indent=2 if a.pretty else None))
        return 0 if a.catalog or out["status"]=="healthy" else 1
    except (OSError,json.JSONDecodeError,ValueError) as e:
        print(json.dumps({"schema":"csr-120/v1","error":str(e)},ensure_ascii=False),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
