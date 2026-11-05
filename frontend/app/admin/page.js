"use client";
import AmendmentAllowance from '@/components/admin/AmendmentAllowance';
import ManageArticles from '@/components/admin/ManageArticles';
import SideBar from '@/components/admin/SideBar';
import DatasetCombine from '@/components/admin/DatasetCombine';
import DatasetGenrator from '@/components/admin/DatasetGenrator';
import MarkdownConverter from '@/components/admin/MarkdownConverter';
import ModelPretraining from '@/components/admin/ModelPretraining';

import {useEffect, useState} from 'react';

export default function Page() {

    const [page, setPage] = useState('markdown-converter');

    return (
        <SideBar page={page} setPage={setPage}>
            
            {page === 'markdown-converter' &&
                <MarkdownConverter />
            }
        </SideBar>  
    )
}
