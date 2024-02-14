import multitasking
import os,time
from rdflib import Graph,URIRef,Literal
from rdflib.namespace import RDF
import signal

"""
De la composition, garder une liste des assets et proposer d'enlever des assets de la chaine
en les enlevant de l'ontologie avec rdf lib asset et tache et on enleve que la tache
"""
base_onto = "http://www.enit.fr/COMPAAS/"
sosa = "http://www.w3.org/ns/sosa/"
"""
1- insert new elements in the ontology
2- Recompose
3- Restart client and server
Steps 2 and 3 only in the case of an emergency on the chain but also remove
broken asset from the ontology: unlink tasks for which this asset is not
suitable anymore.
"""
@multitasking.task
def register_asset(asset_file):
    asset_desc = open (asset_file,'r')
    for line in asset_desc.readlines():
        if line[0] == "!":
            continue
        if "Asset Name:" in line:
            name_asset = filter_line(line)
            name_asset_uri = URIRef(base_onto+name_asset)
            print(name_asset_uri)
        if "Asset Type:" in line:
            type_asset = filter_line(line)
            type_asset_uri = URIRef(sosa+type_asset)
            g.add((name_asset_uri, RDF.type, type_asset_uri))
        if "Driver:" in line:
            drive = filter_line(line)
            drive_uri = URIRef(base_onto+drive)
            g.add((name_asset_uri, URIRef(base_onto+"hasDriver"), drive_uri))
        if "Task:" in line:
            task = filter_line(line)
            task_uri = URIRef(base_onto+task)
            if type_asset == "Sensor":
                g.add((task_uri, URIRef(sosa+"madeBySensor"), name_asset_uri))
            if type_asset == "Actuator":
                g.add((task_uri, URIRef(sosa+"madeByActuator"), name_asset_uri))
        if "Kpi:" in line:
            kpi = str(time.time()).split(".")[0]
            kpi_uri = URIRef(base_onto+kpi)
            g.add((name_asset_uri, URIRef(base_onto+"hasKpi"),kpi_uri))
        if "KpiParam:" in line:
            param = filter_line(line)
            param_uri = URIRef(base_onto+param)
            g.add((kpi_uri, URIRef(base_onto+"iscombinedToParam"),param_uri))
        if "KpiUnit:" in line:
            unit = filter_line(line)
            unit_uri = URIRef(base_onto+unit)
            g.add((kpi_uri, URIRef(base_onto+"iscombinedToUnit"),unit_uri))
        if "KpiValue:" in line:
            value = filter_line(line)
            g.add((kpi_uri, URIRef(base_onto+"value"),Literal(value)))
    composition(g)
    
def filter_line(line_to_filter):
    return line_to_filter.split(":")[1].replace("\n","").rstrip(" ")

def composition(g):
    real_serv = open("Composition_Server.py",'w')
    real_client = open("Composition_Client.py",'w')
    q = """
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        PREFIX aco: <http://www.enit.fr/COMPAAS/>

        SELECT DISTINCT ?procedure ?sensor ?param ?v
        WHERE {
            {?procedure sosa:madeBySensor ?sensor .} UNION {?procedure sosa:madeByActuator ?sensor .} UNION {?procedure 
    aco:madeBySoftware ?sensor .}
            OPTIONAL  {
                ?procedure aco:UsesKpi ?kpi .
                ?kpi aco:isCombinedToParam ?param .
                ?kpi2 aco:isCombinedToParam ?param .
                ?sensor aco:hasKpi ?kpi2 .
                ?kpi2 aco:value ?v .
                }
        }
    """
    base_onto = "http://www.enit.fr/COMPAAS/"
    task_asset = {}
    task_asset_kpi = {}
    result = 0
    for r in g.query(q):
        proc = str(r["procedure"])
        sensor = str(r["sensor"])
        param = str(r["param"])
        value=str(r["v"])
        if param != "None":
            if proc in task_asset_kpi:
                task_asset_kpi[proc].append([param,sensor,value])
            else: 
                task_asset_kpi[proc] = [[param,sensor,value]]
            result += 1
            #print(task_asset_kpi)
            kpi_asset = {}
            for task in task_asset_kpi:
                for criteria in task_asset_kpi[task]:
                    if criteria[0] in kpi_asset:
                        kpi_asset[criteria[0]].append ([criteria[1],criteria[2]])
                    else:
                        kpi_asset[criteria[0]] = [[criteria[1],criteria[2]]]
                #print(kpi_asset)
                scores = {}
                for kpi in kpi_asset:
                    #print("kpi:")
                    #print(kpi)
                    #print(kpi_asset[kpi])
                    for elt in kpi_asset[kpi]:
                        asset = elt[0]
                        score = float(elt[1])
                        #print(asset)
                        #print(score)
                        if asset in scores:
                            scores[asset]+=score
                        else:
                            scores[asset]=score
                current_score = 0
                final_asset = ""
                for asset in scores:
                    if score > current_score:
                        final_asset = asset
                        current_score = score
                task_asset[task.replace(base_onto,"")] = asset.replace(base_onto,"")
        else:
            task_asset[proc.replace(base_onto,"")] = sensor.replace(base_onto,"")
    print("Tasks ASSETS")
    print(task_asset)

    serv = open("OPCUA_Server_skeleton.py",'r')
    client = open("OPCUA_Client_skeleton.py",'r')
    for line in serv.readlines():
        real_serv.write(line)
    serv.close()
    for line in client.readlines():
        real_client.write(line)
    client.close()
    """ Initalize outputs """
    q3 = """
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX ssn: <http://www.w3.org/ns/ssn/>
    PREFIX aco: <http://www.enit.fr/COMPAAS/>
    SELECT DISTINCT ?output
    WHERE {?elt ssn:hasOutput ?output .}
    """
    for r3 in g.query(q3):
        output = str(r3["output"].replace(base_onto,""))
        real_client.write("        "+output+" = 0\n")
    real_client.write("        while 1:\n")

    assets_drivers = []
    for task in task_asset:
        asset = task_asset[task]
        print(asset)
        q3 = """
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        PREFIX ssn: <http://www.w3.org/ns/ssn/>
        PREFIX aco: <http://www.enit.fr/COMPAAS/>
        SELECT DISTINCT ?driver
        WHERE {
        {aco:%s aco:hasDriver ?driver .}
        }
        """ % (asset)
        for r3 in g.query(q3):
            driver = str(r3["driver"].replace(base_onto,""))
            if [asset,driver] not in assets_drivers:
                print(asset+ " driver "+driver)
                assets_drivers.append([asset,driver])
                real_serv.write("import "+driver+"\n")
    q3 = """
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX ssn: <http://www.w3.org/ns/ssn/>
    PREFIX aco: <http://www.enit.fr/COMPAAS/>
    SELECT DISTINCT ?software
    WHERE {
    {?software rdf:type aco:SoftwareAgent .}
    }
    """
    for r3 in g.query(q3):
        soft = str(r3["software"].replace(base_onto,""))
        real_serv.write("import "+soft+"\n")
        assets_drivers.append([soft,soft])

    real_serv.write("\n")
    for asset in assets_drivers:
        real_serv.write("New_composition_"+asset[0]+" = "+asset[1]+"."+asset[1]+"()\n")

    output_returning = []
    registered_tasks = []
    managed_outputs = []
    tasks_io = {}
    soft_called = []
    for task in task_asset:
        q = """
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        PREFIX ssn: <http://www.w3.org/ns/ssn/>
        PREFIX aco: <http://www.enit.fr/COMPAAS/>
        SELECT DISTINCT ?opvar ?trigg ?procedure ?driver ?input ?softproc ?output ?output_procalled ?softout ?myinput
        WHERE {
                aco:%s rdf:type sosa:Procedure
        OPTIONAL {aco:%s ssn:hasInput ?myinput .}
        OPTIONAL {
                aco:%s ssn:detects ?opvar .
                ?opvar aco:triggers ?procedure .
                ?opvar aco:triggerValue ?trigg .
        }
        OPTIONAL { aco:%s ssn:hasOutput ?output .}
        OPTIONAL {
                 ?procedure aco:triggers ?softproc .
                 ?procedure ssn:hasOutput ?output_procalled .
                 ?softproc aco:madeBySoftware ?driver .
                 ?softproc ssn:hasInput ?input .
                 ?softproc ssn:hasOutput ?softout .
        }
         }
        """ % (task,task,task,task)
        for r in g.query(q):
            triggervalue = str(r["trigg"])
            triggervalue = triggervalue.replace(base_onto,"")
            procedure_called = str(r["procedure"])
            procedure_called = procedure_called.replace(base_onto,"")
            output_procalled  = str(r["output_procalled"])
            output_procalled  = output_procalled.replace(base_onto,"")
            inpt = str(r["input"])
            inpt = inpt.replace(base_onto,"")
            myinput = str(r["myinput"])
            myinput = myinput.replace(base_onto,"")
            output = str(r["output"])
            output = output.replace(base_onto,"")
            softout = str(r["softout"])
            softout = softout.replace(base_onto,"")
            driver = str(r["driver"])
            driver = driver.replace(base_onto,"")
            softproc = str(r["softproc"])
            softproc = softproc.replace(base_onto,"")
            #print("task:"+task+" triggers "+procedure_called+" with input: "+inpt+" and driver: "+driver+" for softproc: "+softproc)
            asset = task_asset[task]
            if triggervalue != "None":
                print("If "+task+ " returns "+str(r["trigg"])+" then "+str(r["procedure"].replace(base_onto,"")))
                if myinput != "None":
                    real_serv.write("\n@uamethod\ndef "+task+"(parent,myinput):\n    return New_composition_"+asset+"."+task+"(myinput)\n")
                    output_returning.append(task)
                else:
                    real_serv.write("\n@uamethod\ndef "+task+"(parent):\n    return New_composition_"+asset+"."+task+"()\n")
                    output_returning.append(task)
                if output != "None":
                    if output not in managed_outputs:
                        real_client.write("""            %s = await client.nodes.objects.call_method(f"{nsidx}:%s")\n"""%(output,task))
                        managed_outputs.append(output)
                    real_client.write("""            if %s == %s:\n"""%(output,triggervalue))
                else:
                    real_client.write("""            %sMonitor = await client.nodes.objects.call_method(f"{nsidx}:%s")\n"""%(task,task))
                    real_client.write("""            if %sMonitor == %s:\n"""%(task,triggervalue))
                if softproc == "None":
                    real_client.write("""                %sRes = await client.nodes.objects.call_method(f"{nsidx}:%s")\n"""%(task,procedure_called))
            if softproc != "None" and softproc not in soft_called:
                print("BESIDES, If "+procedure_called+ " is executed then lauch "+softproc+" with driver "+driver+" and input "+inpt)
                real_client.write("""                %s = await client.nodes.objects.call_method(f"{nsidx}:%s")\n"""%(output_procalled,procedure_called))
                real_client.write("""                %s = await client.nodes.objects.call_method(f"{nsidx}:%s",%s)\n"""%(softout,softproc,output_procalled))
                soft_called.append(softproc)
                #managed_outputs.append(output_procalled)
                managed_outputs.append(softout)

    for task in output_returning:
        try:
            del task_asset[task]
            registered_tasks.append(task)
        except:
            pass
    for task in task_asset:
        asset = task_asset[task]
        real_serv.write("\n@uamethod\ndef "+task+"(parent):\n    return New_composition_"+asset+"."+task+"()\n")
        registered_tasks.append(task)

    real_serv.write("\n")
    serv = open("OPCUA_Server_skeleton_part2.py",'r')
    for line in serv.readlines():
        real_serv.write(line)
    serv.close()

    for task in registered_tasks:
        real_serv.write("""    await server.nodes.objects.add_method(ua.NodeId("%s", idx),ua.QualifiedName("%s", idx),%s,[ua.VariantType.Int64],[ua.VariantType.Int64])\n"""%(task,task,task))

    serv = open("OPCUA_Server_skeleton_part3.py",'r')
    for line in serv.readlines():
        real_serv.write(line)
    serv.close()

    real_client.write("""if __name__ == "__main__":\n    asyncio.run(main())""")
    real_serv.close()
    real_client.close()
    return task_asset
    
@multitasking.task
def run_server():
    os.system("python ./Composition_Server.py")

@multitasking.task
def run_client():
    os.system("python ./Composition_Client.py")

def delete_functionality():
    q = """
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX aco: <http://www.enit.fr/COMPAAS/>
    SELECT DISTINCT ?procedure ?sensor
    WHERE {
    {?procedure sosa:madeBySensor ?sensor .} UNION {?procedure sosa:madeByActuator ?sensor .}
    }
    """
    proc_sensor=[]
    for r in g.query(q):
        proc = str(r["procedure"]).replace(base_onto,"")
        sensor = str(r["sensor"]).replace(base_onto,"")
        proc_sensor.append([proc,sensor])
    count = -1
    print(proc_sensor)
    for elt in range (len(proc_sensor)):
        count += 1
        print(str(count)+":delete "+str(proc_sensor[elt][0]) + " for asset:" + str(proc_sensor[elt][1]))
    choice = input("Cancel:c\nYour choice:")
    prcdr = proc_sensor[int(choice)][0]
    eqpt = proc_sensor[int(choice)][1]
    g.remove((URIRef(base_onto+prcdr),URIRef(sosa+"madeBySensor"),URIRef(base_onto+eqpt)))
    g.remove((URIRef(base_onto+prcdr),URIRef(sosa+"madeByActuator"),URIRef(base_onto+eqpt)))
    nb_iter = 0
    for elt in range (len(proc_sensor)):
        if str(proc_sensor[elt][0]) == prcdr:
            nb_iter += 1
    if nb_iter == 1:
        print("BEWARE: Procedure"+prcdr+" Can no more be achieved")

def stop_exec():
    order = "kill $(ps -aux | grep 'python ./Composition_Server.py'|awk '{print $2}')"
    os.system(order)
    order = "kill $(ps -aux | grep 'python ./Composition_Client.py'|awk '{print $2}')"
    os.system(order)
    
g = Graph().parse("COMPAK")
composition(g)
userchoice = "None"

while (userchoice!="q"):
    userchoice = input("What would you like to do:\n\
    Compose the production chain: c\n\
    Run the production chain:r\n\
    Add new asset in the chain: n\n\
    Delete the ability for an asset to conduct a procedure:d\n\
    Quit:q\n")
    if userchoice == "c":
        composition(g)
    elif userchoice == "r":
        stop_exec()
        signal.signal(signal.SIGINT, multitasking.killall)
        run_server()
        time.sleep(20)
        run_client()
    elif userchoice == "n":
        register_asset("assetExample.txt")
    elif userchoice == "d":
        delete_functionality()
    elif userchoice == "q":
        stop_exec()
        exit()
    else:
        print("unknown command:%s",userchoice)
