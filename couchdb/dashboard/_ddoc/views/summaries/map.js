function(doc) {
  if (doc.type == "slot-build") {
    emit([doc.slot, doc.build_id, doc.platform],
         {"host": doc.host,
          "job_id": doc.job_id,
          "started": doc.started,
          "completed": doc.completed});
    for(var idx in doc.summary) {
      emit([doc.slot, doc.build_id, doc.platform],
           {project: doc.summary[idx].project,
            build: {warnings: doc.summary[idx].build[0],
            	    errors: doc.summary[idx].build[1]}
            });
      emit([doc.slot, doc.build_id, doc.platform],
              {project: doc.summary[idx].project,
               tests: {failed: doc.summary[idx].tests[0],
                   	total: doc.summary[idx].tests[1]}
               });
    }
  }
}
